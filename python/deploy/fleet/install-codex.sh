#!/usr/bin/env bash
# Install or update the Codex CLI on a fleet node.
# Usage: ./install-codex.sh [node]
#   no arg  -> run on localhost
#   <node>  -> ssh into node and install there
set -euo pipefail

install_local() {
  echo "[*] $(hostname): ensuring codex CLI up to date"
  if ! command -v node >/dev/null 2>&1; then
    echo "[*] installing Node.js"
    if command -v apt-get >/dev/null 2>&1; then
      curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null \
        && sudo apt-get install -y nodejs
    elif command -v snap >/dev/null 2>&1; then
      sudo snap install node --classic 2>/dev/null || true
    fi
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "[!] npm not available after Node install — aborting"
    return 1
  fi
  sudo npm install -g @openai/codex@latest 2>&1 | tail -1
  echo "[+] codex $(codex --version 2>&1) on $(hostname)"
}

if [ $# -eq 0 ]; then
  install_local
else
  NODE="$1"
  echo "=== $NODE ==="
  ssh -o ConnectTimeout=10 "$NODE" "$(declare -f install_local); install_local" \
    || echo "[!] $NODE unreachable"
fi
