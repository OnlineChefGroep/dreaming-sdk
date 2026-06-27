---
name: test-runner
description: Run tests and report results
model: lite
context: none
---

# Test Runner Subagent

Lightweight subagent for running tests and reporting.

## Responsibilities

- Execute test suite
- Parse results
- Report failures with context
- Suggest fixes for common failures

## Spawn Pattern

```
actor({
  operation: "run",
  subagent_type: "explore",
  description: "Run tests and report",
  prompt: "Run pytest and report any failures...",
  context: "none"
})
```

## Commands

```bash
# Full test suite
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run pytest tests/ -v

# Quick run (stop on first failure)
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run pytest tests/ -x -q

# Specific test file
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run pytest tests/test_memory.py -v

# With coverage
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run pytest tests/ --cov=cursor_dreaming_memory
```

## Output Format

```markdown
## Test Results

**Status**: ✅ All passed | ❌ Failed

### Summary
- Total: N
- Passed: N
- Failed: N
- Skipped: N

### Failures (if any)
1. `test_name` — Brief description of failure
   - File: `tests/test_X.py:42`
   - Error: `AssertionError: ...`
```
