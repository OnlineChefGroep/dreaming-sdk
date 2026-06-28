#!/usr/bin/env bash
# Sync agent-memory env (DSN + secrets) to all fleet nodes over Tailscale.
# Usage: ./sync-env.sh [--rotate] [node ...]   (defaults to all known nodes)
# Encryption uses SECRETS_ENCRYPTION_KEY env var (generate with: openssl rand -hex 32)
set -euo pipefail

ROTATE_KEY=false
if [[ "${1:-}" == "--rotate" ]]; then
  ROTATE_KEY=true
  shift
fi

NODES=("${@:-bc-scan-arm bc-scan-2 bc-scan-1 bc-monitor}")
SRC="${HOME}/.openclaude/.env"
REMOTE_ENV="/home/ubuntu/.agent-memory.env"
ENCRYPTED_SUFFIX=".enc"

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: $SRC not found" >&2
  exit 1
fi

if [[ -z "${SECRETS_ENCRYPTION_KEY:-}" ]]; then
  echo "ERROR: SECRETS_ENCRYPTION_KEY env var not set" >&2
  echo "Generate one with: openssl rand -hex 32" >&2
  exit 1
fi

if [[ "$ROTATE_KEY" == true ]]; then
  echo "Key rotation mode: will generate and save new encryption key"
  NEW_KEY=$(openssl rand -hex 32)
  echo "New key generated. Update your env with:"
  echo "export SECRETS_ENCRYPTION_KEY=$NEW_KEY"
fi

# Only ship the keys the memory layer needs (never the full secrets file).
KEYS=(AGENT_MEMORY_DATABASE_URL LINEAR_API_KEY LINEAR_TEAM_KEY NOTION_API_KEY NOTION_TOKEN \
      CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID R2_BUCKET R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_ENDPOINT \
      SENTRY_DSN SENTRY_ENVIRONMENT)

TMP="$(mktemp)"
ENCRYPTED_TMP="${TMP}${ENCRYPTED_SUFFIX}"
# shellcheck disable=SC1090
source "$SRC"
for k in "${KEYS[@]}"; do
  v="${!k:-}"
  [[ -n "$v" ]] && echo "export $k=\"$v\"" >> "$TMP"
done

echo "Encrypting env file with AES-256-CBC..."
openssl enc -aes-256-cbc -salt -pbkdf2 -in "$TMP" -out "$ENCRYPTED_TMP" -k "$SECRETS_ENCRYPTION_KEY"

for node in ${NODES[@]}; do
  echo "→ $node"
  scp -q "$ENCRYPTED_TMP" "$node:${REMOTE_ENV}${ENCRYPTED_SUFFIX}"
  ssh "$node" "openssl enc -d -aes-256-cbc -pbkdf2 -in ${REMOTE_ENV}${ENCRYPTED_SUFFIX} -out ${REMOTE_ENV} -k '$SECRETS_ENCRYPTION_KEY' && rm -f ${REMOTE_ENV}${ENCRYPTED_SUFFIX}"
  # Ensure interactive + non-interactive shells load it
  ssh "$node" "grep -q 'agent-memory.env' ~/.bashrc 2>/dev/null || echo '[ -f ~/.agent-memory.env ] && . ~/.agent-memory.env' >> ~/.bashrc"
done
rm -f "$TMP" "$ENCRYPTED_TMP"
echo "Done. Memory env synced to: ${NODES[*]}"
