---
name: dream-tui
description: Interactive terminal control surface for the dreaming plugin, plus an agent JSON protocol. Drives doctor, test, eval, run, status, scope, index, and which through the dream CLI. Read-only with respect to soul.md and live memory.
---

# dream-tui (Codex)

Reference copy of the dream terminal control surface for Codex-style hosts.

Shared UX contract: [shared/tui-ux.md](../../shared/tui-ux.md).
Special agent: [agents/dream-navigator](./agents/openai.yaml).

## Human surface

```bash
dream            # interactive TUI (real TTY)
dream tui        # explicit
```

Keys: `↑/↓` or `j/k` move · `enter` run · `/` palette · `esc` back · `q` quit.

## Agent surface

```bash
dream agent --json          # readiness + recommended next actions
dream capabilities --json   # command matrix
dream run --json            # test -> eval -> decisions
dream run --dry-run --json  # plan only
```

## Boundaries

- Never read or mutate `soul.md` or live `~/.cursor/dreaming/` state.
- Eval output is confined to `eval/results/<run_id>/`.
- Drive via JSON; never screen-scrape the rendered frame.
- Plugin lives at `~/.cursor/plugins/local/dreaming/` (`DREAM_PLUGIN_ROOT` to override).
