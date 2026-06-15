#!/usr/bin/env bash
# Install dream-eval-loop skills for multiple agent platforms.
# Usage: ./install-dream-skills.sh --platform codex --target ~/my-repo
#        ./install-dream-skills.sh --platform all --global

set -euo pipefail

PLATFORM="all"
TARGET="$(pwd)"
GLOBAL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM="$2"; shift 2 ;;
    --target)   TARGET="$2"; shift 2 ;;
    --global)   GLOBAL=1; shift ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

BUNDLE_ROOT="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_CLI="${HOME}/.cursor/plugins/local/dreaming/cli/dream.mjs"

if [[ ! -f "$PLUGIN_CLI" ]]; then
  echo "WARN: dreaming plugin not found at $PLUGIN_CLI" >&2
fi

install_one() {
  local name="$1" src_rel="$2" dst
  case "$name" in
    cursor)
      if [[ $GLOBAL -eq 1 ]]; then dst="${HOME}/.cursor/skills/dream-eval-loop"
      else dst="${TARGET}/.cursor/skills/dream-eval-loop"; fi ;;
    claude)
      if [[ $GLOBAL -eq 1 ]]; then dst="${HOME}/.claude/skills/dream-eval-loop"
      else dst="${TARGET}/.claude/skills/dream-eval-loop"; fi ;;
    codex)    dst="${TARGET}/.agents/skills/dream-eval-loop" ;;
    opencode) dst="${TARGET}/.opencode/skills/dream-eval-loop" ;;
    grok)     dst="${TARGET}/.factory/skills/dream-eval-loop" ;;
    *) echo "Unknown platform: $name"; exit 2 ;;
  esac
  local src="${BUNDLE_ROOT}/${src_rel}"
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
  echo "Installed $name -> $dst"
}

PLATFORMS=()
if [[ "$PLATFORM" == "all" ]]; then
  PLATFORMS=(cursor claude codex opencode grok)
else
  PLATFORMS=("$PLATFORM")
fi

for p in "${PLATFORMS[@]}"; do
  case "$p" in
    cursor)   install_one cursor   "cursor/skills/dream-eval-loop" ;;
    claude)   install_one claude   "claude/skills/dream-eval-loop" ;;
    codex)    install_one codex    "codex/skills/dream-eval-loop" ;;
    opencode) install_one opencode "opencode/skills/dream-eval-loop" ;;
    grok)     install_one grok     "grok/skills/dream-eval-loop" ;;
  esac
done

SHARED_DST="${TARGET}/docs/ops/dreaming/skills-bundle/shared"
if [[ ! -d "$SHARED_DST" ]]; then
  mkdir -p "$SHARED_DST"
  cp -R "${BUNDLE_ROOT}/shared/"* "$SHARED_DST/"
  echo "Copied shared/ -> $SHARED_DST"
fi

echo "Done. Verify: node $PLUGIN_CLI test --json"
