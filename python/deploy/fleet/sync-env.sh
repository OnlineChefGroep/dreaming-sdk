#!/usr/bin/env bash
# Sync agent-memory env (DSN + secrets) to all fleet nodes over Tailscale.
# Usage: ./sync-env.sh [node ...]   (defaults to all known nodes)
set -euo pipefail

NODES=("${@:-bc-scan-arm bc-scan-2 bc-scan-1 bc-monitor}")
SRC="${HOME}/.openclaude/.env"
REMOTE_ENV="/home/ubuntu/.agent-memory.env"

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: $SRC not found" >&2
  exit 1
fi

# Only ship the keys the memory layer needs (never the full secrets file).
KEYS=(AGENT_MEMORY_DATABASE_URL LINEAR_API_KEY LINEAR_TEAM_KEY NOTION_API_KEY NOTION_TOKEN \
      CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID R2_BUCKET R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_ENDPOINT \
      SENTRY_DSN SENTRY_ENVIRONMENT)

TMP="$(mktemp)"
# shellcheck disable=SC1090
source "$SRC"
for k in "${KEYS[@]}"; do
  v="${!k:-}"
  [[ -n "$v" ]] && echo "export $k=\"$v\"" >> "$TMP"
done

for node in ${NODES[@]}; do
  echo "→ $node"
  scp -q "$TMP" "$node:$REMOTE_ENV"
  # Ensure interactive + non-interactive shells load it
  ssh "$node" "grep -q 'agent-memory.env' ~/.bashrc 2>/dev/null || echo '[ -f ~/.agent-memory.env ] && . ~/.agent-memory.env' >> ~/.bashrc"
done
rm -f "$TMP"
echo "Done. Memory env synced to: ${NODES[*]}"
