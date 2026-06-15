#!/usr/bin/env bash
# Idempotent installer: wire the agent memory layer into one fleet host.
# Connects every code-agent CLI on the host to the shared OCI Postgres SSOT.
#
# Usage (from sofie control node):
#   for h in bc-monitor bc-scan-arm bc-scan-2; do
#     scp -r python "$h:~/cursor-dreaming-memory"
#     ssh "$h" 'bash ~/cursor-dreaming-memory/deploy/fleet/install-memory.sh'
#   done
#
# Secrets are read at runtime from ~/.config/agent-memory/.env on each host.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/cursor-dreaming-memory}"
ENV_DIR="$HOME/.config/agent-memory"
ENV_FILE="$ENV_DIR/.env"

echo "[*] Installing agent memory on $(hostname)"

# 1. uv
if ! command -v uv >/dev/null 2>&1; then
  echo "[*] Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Python deps
cd "$REPO_DIR"
uv sync --extra all

# 3. Secrets file (filled out-of-band; never committed)
mkdir -p "$ENV_DIR"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'EOF'
# Per-host agent memory secrets (chmod 600). Fill these in.
AGENT_MEMORY_DATABASE_URL=
LINEAR_API_KEY=
NOTION_API_KEY=
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_ACCOUNT_ID=
SENTRY_DSN=
SENTRY_ENVIRONMENT=fleet
EOF
  chmod 600 "$ENV_FILE"
  echo "[!] Created $ENV_FILE — fill in secrets, then re-run doctor."
fi

# 4. Verify
set +e
FLEET_ENV_FILE="$ENV_FILE" uv run dream-memory doctor
echo "[*] Done. Agents on this host can now: uv run --project $REPO_DIR dream-memory ..."
