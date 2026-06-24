---
name: dream-tui
description: Interactive terminal control surface for the dreaming plugin. Opens an antigravity-style full-screen TUI for humans (menu, command palette, live plugin status) and exposes a stable JSON protocol for agents. Drives doctor, test, eval, run, status, scope, index, and which through the dream CLI. Does NOT mutate soul.md or live memory.
disable-model-invocation: false
inherits: [dream-eval]
user: enabled
---

# dream-tui (Cursor)

A single command model, two surfaces: a polished interactive terminal UI for
humans and a machine-readable protocol for agents. Both are served by the
`@onlinechefgroep/dream-cli` package in this repo (`bin/dream.js` →
`lib/dream-cli.js` + `lib/dream-tui.js`).

Full UX contract: [shared/tui-ux.md](../../shared/tui-ux.md).

## When to use this skill

- A human wants to drive the dreaming plugin interactively from a terminal.
- An agent wants to discover capabilities and run the dream flow deterministically.
- You need a fast `doctor` / `run` / `eval --dry-run` loop without memorizing flags.

## Human surface

```bash
dream            # opens the interactive TUI in a real TTY
dream tui        # same, explicit
```

Navigation:

- `↑/↓` or `j/k` — move
- `enter` — run the highlighted command
- `/` — open the fuzzy command palette
- `esc` — leave the palette
- `q` or `Ctrl-C` — quit

The header always shows whether the dreaming plugin was discovered, so the human
never acts on a missing plugin by accident.

## Agent surface

```bash
dream agent --json          # readiness + recommended next actions
dream capabilities --json   # full command matrix
dream run --json            # test -> eval -> decisions, machine-readable
dream run --dry-run --json  # plan only, no plugin execution required
dream tui --json            # the exact human menu model (for UI mirroring)
```

Agents must read JSON, not the rendered frame. See the special agent
[`dream-navigator`](./agents/dream-navigator.md) for the recommended persona.

## Commands

| Command | Purpose |
|---------|---------|
| `dream doctor [--json]` | Plugin discovery + runtime support |
| `dream which [--json]` | Resolved plugin CLI path |
| `dream test` | Deterministic gates (hard-fail stops the loop) |
| `dream eval [--dry-run]` | Prepare/preview a golden eval run |
| `dream run [--json]` | High-level test → eval → decisions flow |
| `dream status` / `scope` / `index` | Live diagnostics (pass-through) |
| `dream cloud [...]` | Run the SDK cloud wrapper (recursion-guarded) |

## Plugin requirement

The dreaming plugin is an external local install at
`~/.cursor/plugins/local/dreaming/`. Set `DREAM_PLUGIN_ROOT` to override. This
skill never vendors or mutates the plugin; it only orchestrates it.

## Boundaries

- Read-only with respect to `soul.md` and live `~/.cursor/dreaming/` state.
- Eval output belongs to `eval/results/<run_id>/` only.
- Never commit secrets, PII, or live decision logs (see [AGENTS.md](../../../../AGENTS.md)).
