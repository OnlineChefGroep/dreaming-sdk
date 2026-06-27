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

skill_base() {
  # Print the destination skills directory for a platform.
  case "$1" in
    cursor)
      if [[ $GLOBAL -eq 1 ]]; then echo "${HOME}/.cursor/skills"; else echo "${TARGET}/.cursor/skills"; fi ;;
    claude)
      if [[ $GLOBAL -eq 1 ]]; then echo "${HOME}/.claude/skills"; else echo "${TARGET}/.claude/skills"; fi ;;
    codex)    echo "${TARGET}/.agents/skills" ;;
    opencode) echo "${TARGET}/.opencode/skills" ;;
    grok)     echo "${TARGET}/.factory/skills" ;;
    *) echo "Unknown platform: $1" >&2; exit 2 ;;
  esac
}

install_skill() {
  local platform="$1" skill="$2"
  local src="${BUNDLE_ROOT}/${platform}/skills/${skill}"
  if [[ ! -d "$src" ]]; then
    return 0  # this platform does not ship this skill
  fi
  local dst="$(skill_base "$platform")/${skill}"
  mkdir -p "$(dirname "$dst")"
  rm -rf "$dst"
  cp -R "$src" "$dst"
  echo "Installed ${platform}/${skill} -> $dst"
}

PLATFORMS=()
if [[ "$PLATFORM" == "all" ]]; then
  PLATFORMS=(cursor claude codex opencode grok)
else
  PLATFORMS=("$PLATFORM")
fi

SKILLS=(dream-eval-loop dream-tui)

for p in "${PLATFORMS[@]}"; do
  for s in "${SKILLS[@]}"; do
    install_skill "$p" "$s"
  done
done

SHARED_DST="${TARGET}/docs/ops/dreaming/skills-bundle/shared"
mkdir -p "$SHARED_DST"
rm -rf "${SHARED_DST:?}/"*
cp -R "${BUNDLE_ROOT}/shared/"* "$SHARED_DST/"
echo "Copied shared/ -> $SHARED_DST"

echo "Done. Verify: node $PLUGIN_CLI test --json"
