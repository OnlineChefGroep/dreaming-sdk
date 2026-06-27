---
name: test-all
description: Run lint and tests for both dream-eval and dreaming-memory packages. Use after any code change to verify nothing is broken across the monorepo.
tools: bash
---

# Test All Packages

Run lint + tests for both packages in the monorepo, reporting results for each.

## Steps

1. **Lint + test dream-eval**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/dream-eval && uv run ruff check src/ tests/ && uv run pytest tests/ -v
   ```

2. **Lint + test dreaming-memory**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run ruff check src/ tests/ && uv run pytest tests/ -v
   ```

3. **Report combined result**
   - Summarize pass/fail per package
   - If any fail: show first 20 lines of failure output
   - If all pass: "All 219 tests pass across both packages"

## When to Use

- After editing files in either package
- Before committing changes
- After pulling latest changes
- As a final check before release

## Notes

- dream-eval lives at `dream-eval/`, dreaming-memory at `python/`
- Each has its own venv managed by uv
- ruff config: line-length=100, target-version=py311
