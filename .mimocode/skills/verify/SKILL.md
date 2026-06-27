---
name: verify
description: Run lint and tests for a specific package. For both packages at once, use test-all instead.
tools: bash
---

# Verify Code Quality

Run linting and tests for a single package to verify code changes are clean.

## Steps

1. **Run ruff linter**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/<package> && uv run ruff check src/ tests/
   ```

2. **Run pytest**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/<package> && uv run pytest tests/ -v
   ```

3. **Report results**
   - If both pass: "Lint and tests pass"
   - If lint fails: Show errors and offer to fix with `--fix`
   - If tests fail: Show failures and investigate

## When to Use

- After editing files in a single package
- Before committing changes to one package
- When investigating test failures in a specific package

## Notes

- Package paths: `dream-eval` or `python` (for dreaming-memory)
- Uses `uv run` for correct virtual environment
- ruff config: line-length=100, target-version=py311
- For both packages: use `test-all` skill instead
