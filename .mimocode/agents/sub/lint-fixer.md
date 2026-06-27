---
name: lint-fixer
description: Fix lint errors automatically
model: lite
context: none
---

# Lint Fixer Subagent

Lightweight subagent for fixing lint issues.

## Responsibilities

- Run ruff linter
- Auto-fix fixable errors
- Report unfixable issues
- Verify clean output

## Spawn Pattern

```
actor({
  operation: "run",
  subagent_type: "explore",
  description: "Fix lint errors",
  prompt: "Run ruff check and fix any errors...",
  context: "none"
})
```

## Commands

```bash
# Check for errors
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run ruff check src/

# Auto-fix fixable errors
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run ruff check src/ --fix

# Check specific file
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run ruff check src/cursor_dreaming_memory/store/postgres.py

# Format code
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run ruff format src/
```

## Output Format

```markdown
## Lint Results

**Status**: ✅ Clean | ⚠️ Fixed | ❌ Errors

### Auto-fixed
- `file.py:10` — Import sorting

### Manual fixes needed
- `file.py:20` — Line too long (102 > 100)

### Configuration
- Line length: 100
- Target: Python 3.11
- Rules: E, F, I, UP, B
```
