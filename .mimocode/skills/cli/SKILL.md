---
name: cli
description: CLI expert for command development, testing, and user experience
tools: read, edit, bash, grep, glob
model: standard
---

# CLI Subagent

Expert for the dream-memory CLI tool.

## Responsibilities

- Command development and testing
- Argument parsing and validation
- Output formatting
- Error handling
- Documentation

## Key Files

- `python/src/cursor_dreaming_memory/cli.py` — Main CLI entrypoint
- `python/src/cursor_dreaming_memory/dashboard.py` — FastAPI metrics server
- `python/pyproject.toml` — Script entry point: `dream-memory`

## Commands

```bash
# Initialize schema
dream-memory init

# Show config + connectivity
dream-memory doctor

# Print metrics as JSON
dream-memory metrics [--days N]

# Triage Linear issues
dream-memory triage [--state NAME] [--limit N] [--apply] [--comment]

# Write memory record
dream-memory remember --session-id ID --content '{"note": "..."}'

# Query memory records
dream-memory recall [--agent A] [--session-id S] [--limit N]

# Ingest Linear issue
dream-memory linear-ingest ISSUE_ID

# Ingest Notion page
dream-memory notion-ingest PAGE_ID

# Export session as Markdown
dream-memory export --session-id ID [--output FILE]

# Post eval report to Slack
dream-memory slack-report [--run-id ID] [--metrics-json PATH]

# Run metrics dashboard
dream-memory serve [--host HOST] [--port PORT]
```

## Patterns

### Context Manager Usage
```python
with AgentMemory() as memory:
    records = memory.recall(session_id="test")
# Pool automatically closed
```

### Output Formatting
- JSON output for machine consumption
- Markdown for human readability
- Errors to stderr with non-zero exit code

### Command Structure
```python
parser = argparse.ArgumentParser(description="...")
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("init", help="Apply Postgres schema")
# ... more commands
```

## Testing

```bash
# Run CLI tests
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run pytest tests/test_export.py -v

# Manual testing
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run dream-memory doctor
```
