---
name: release
description: Build, tag, and push a release for both packages. Handles the full release flow: build wheels, create git tag, push to trigger CI.
tools: bash
---

# Release Packages

Build both packages, create a git tag, and push to trigger the GitHub Actions release workflow.

## Steps

1. **Run tests first** (fail-fast)
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/dream-eval && uv run pytest tests/ -q && cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run pytest tests/ -q
   ```

2. **Build packages**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/dream-eval && uv build
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv build
   ```

3. **Commit any pending changes**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk && git add -A && git commit -m "release: v$VERSION" || echo "Nothing to commit"
   ```

4. **Create tag and push**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk && git tag -a "v$VERSION" -m "Release v$VERSION" && git push origin main && git push origin "v$VERSION"
   ```

5. **Verify release workflow**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk && gh run list --workflow=release.yml --limit=1
   ```

## When to Use

- When cutting a new release
- After all tests pass and changes are committed

## Notes

- GitHub Actions will: build → publish to PyPI → create GitHub Release
- Requires PYPI_TOKEN secret configured in GitHub
- Tag format: `v{major}.{minor}.{patch}` (e.g., `v0.3.0`)
- Check https://github.com/OnlineChefGroep/dreaming-sdk/actions after push
