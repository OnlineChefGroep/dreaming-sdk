#!/usr/bin/env bash
# Release script for cursor-dreaming-sdk
# Usage: ./release.sh <version>
# Example: ./release.sh 0.2.0

set -euo pipefail

VERSION="${1:?Usage: ./release.sh <version>}"

echo "Releasing v${VERSION}..."

# Build packages
echo "Building dream-eval..."
cd dream-eval && uv build && cd ..

echo "Building dreaming-memory..."
cd python && uv build && cd ..

# Create git tag
echo "Creating git tag v${VERSION}..."
git tag -a "v${VERSION}" -m "Release v${VERSION}"

# Push tag (this triggers the release workflow)
echo "Pushing tag to origin..."
git push origin "v${VERSION}"

echo ""
echo "Release v${VERSION} initiated!"
echo ""
echo "GitHub Actions will:"
echo "  1. Build packages"
echo "  2. Publish to PyPI"
echo "  3. Create GitHub Release"
echo ""
echo "Monitor: https://github.com/OnlineChefGroep/cursor-dreaming-sdk/actions"
