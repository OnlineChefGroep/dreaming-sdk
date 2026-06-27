#!/usr/bin/env bash
# Install the cursor-dreaming-memory package on a fleet node and verify the DB link.
# Usage: ./install-agent-memory.sh <node>
set -euo pipefail
NODE="${1:?usage: install-agent-memory.sh <node>}"
REPO_DIR="/home/ubuntu/Orgchefgroep/dreaming-sdk"

ssh "$NODE" bash -s <<'REMOTE'
set -euo pipefail
[ -f ~/.agent-memory.env ] && . ~/.agent-memory.env
command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
mkdir -p ~/Orgchefgroep
if [ ! -d ~/Orgchefgroep/dreaming-sdk ]; then
  gh repo clone OnlineChefGroep/dreaming-sdk ~/Orgchefgroep/dreaming-sdk 2>/dev/null \
    || git clone https://github.com/OnlineChefGroep/dreaming-sdk ~/Orgchefgroep/dreaming-sdk
fi
cd ~/Orgchefgroep/dreaming-sdk/python
git pull --ff-only 2>/dev/null || true
uv sync
echo "--- verifying DB link ---"
uv run python -c "from cursor_dreaming_memory import AgentMemory; m=AgentMemory(enable_sentry=False); print(m.config.redacted()); m.ensure_schema(); print('schema OK')"
REMOTE
echo "Installed agent-memory on $NODE"
