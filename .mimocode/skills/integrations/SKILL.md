---
name: integrations
description: Integration expert for Linear, Notion, Cloudflare, and other external services
tools: read, edit, bash, grep, glob
model: standard
---

# Integrations Subagent

Expert for external service integrations in cursor-dreaming-sdk.

## Responsibilities

- Linear API integration (issues, comments, triage)
- Notion API integration (pages, memory sync)
- Cloudflare R2 storage
- Sentry error tracking
- Slack notifications

## Key Files

- `python/src/dreaming_memory/integrations/linear.py` — LinearClient + LinearMemoryBridge
- `python/src/dreaming_memory/integrations/notion.py` — NotionMemoryBridge
- `python/src/dreaming_memory/integrations/cloudflare.py` — CloudflareR2
- `python/src/dreaming_memory/integrations/slack.py` — SlackClient
- `python/src/dreaming_memory/observability/sentry.py` — Sentry integration

## Patterns

### Linear GraphQL
```python
def gql(self, query: str, variables: dict | None = None) -> dict:
    resp = httpx.post(
        LINEAR_ENDPOINT,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": self.api_key},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})
```

### Memory Bridge Pattern
- Ingest external data → Write to AgentMemoryStore
- Sync bidirectionally with conflict resolution
- Use SessionContext for tracking source

### Lazy Initialization
```python
@property
def linear(self) -> LinearMemoryBridge:
    if self._linear is None:
        self._linear = LinearMemoryBridge(self.store)
    return self._linear
```

## Environment Variables

```bash
# Linear
LINEAR_API_KEY=lin_api_...
LINEAR_TEAM_ID=...
LINEAR_TEAM_KEY=CHEF

# Notion
NOTION_API_KEY=secret_...

# Cloudflare
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...
R2_BUCKET=agent-memory

# Sentry
SENTRY_DSN=...
SENTRY_ENVIRONMENT=development
```
