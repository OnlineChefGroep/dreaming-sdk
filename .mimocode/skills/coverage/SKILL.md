---
name: coverage
description: Measure test coverage for both packages and identify uncovered lines. Use to find gaps before release or when adding new modules.
tools: bash
---

# Measure Test Coverage

Run pytest with coverage for both packages, report percentage and missing lines.

## Steps

1. **Install pytest-cov** (idempotent)
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/dream-eval && uv pip install pytest-cov 2>/dev/null
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv pip install pytest-cov 2>/dev/null
   ```

2. **Coverage for dream-eval**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/dream-eval && uv run pytest tests/ --cov=dream_eval --cov-report=term-missing 2>&1 | tail -15
   ```

3. **Coverage for dreaming-memory**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run pytest tests/ --cov=dreaming_memory --cov-report=term-missing 2>&1 | tail -15
   ```

4. **Report**
   - Show total coverage % per package
   - List modules below 80% coverage
   - Suggest which gaps are testable (vs. requiring external services)

## When to Use

- Before release to check coverage targets
- After adding new modules to assess test needs
- When deciding where to add tests next

## Notes

- dream-eval target: 94%+ (core logic 100%)
- dreaming-memory gaps often require mocked Postgres/Linear/Notion
- Coverage gaps in `postgres.py`, `linear.py`, `notion.py` need `patch.dict(sys.modules)` for psycopg mocking
