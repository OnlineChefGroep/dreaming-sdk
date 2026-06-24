# Dream TUI — terminal UX contract

The `dream` CLI exposes two first-class surfaces driven by the same model:

- **Human surface** — an interactive, full-screen terminal UI (`dream tui`).
- **Agent surface** — a stable, machine-readable protocol (`dream agent --json`,
  `dream capabilities --json`, and `<command> --json`).

This document is the shared UX contract both surfaces honor, so a human and an
autonomous agent navigate the *same* command model.

---

## Design principles (antigravity-style)

1. **Alternate screen buffer.** The interactive UI enters the alternate buffer
   (`\x1b[?1049h`) and restores the user's scrollback on exit. The cursor is
   hidden while interactive and always restored.
2. **One model, two renderers.** Menu items, hints, and plugin status come from a
   single model. Humans see a rendered frame; agents read the same model as JSON.
3. **Motion is predictable.** Selection wraps around. Arrow keys and `j`/`k` move.
   `enter` runs. `/` opens the command palette. `q` / `Ctrl-C` quit.
4. **Fail visibly.** Plugin discovery status is always shown in the header. A
   missing plugin never silently degrades to a fake success.
5. **No runtime dependencies.** Rendering and state reduction are pure functions
   in `lib/dream-tui.js`; the interactive loop only adds raw-mode key reading.

---

## Layout

```
┌ header bar ─ title · plugin status · node version ───────────────┐
  subtitle
  ┌ menu (selection highlight) ┐ │ ┌ detail panel ┐
  │ ▌ Doctor                    │ │   command: dream doctor
  │   Test                      │ │   what it does: ...
  │   Eval dry-run              │ │   plugin root: ~/.cursor/...
  └─────────────────────────────┘ │ └──────────────┘
└ footer ─ keybind hints ──────────────────────────────────────────┘
```

- **Header:** `◆ DREAM` badge, title, right-aligned plugin status + Node version.
- **Menu pane:** the command list; the active row is highlighted with `▌`.
- **Detail pane:** the selected command's invocation, description, and plugin root.
- **Footer:** context-sensitive keybindings (menu vs. palette mode).

---

## Key bindings

| Key | Menu mode | Palette mode |
|-----|-----------|--------------|
| `↑` / `k` | move up | move up |
| `↓` / `j` | move down | move down |
| `enter` | run selected | run selected |
| `/` | open palette | — |
| printable | — | append to query |
| `backspace` | — | delete query char |
| `esc` | — | back to menu |
| `q` / `Ctrl-C` | quit | quit |

The command palette filters items with a small fuzzy matcher (subsequence match,
adjacency-weighted), so `ev` selects **Eval** and `dr` selects **Doctor**.

---

## Commands surfaced

| Item | Command | Notes |
|------|---------|-------|
| Doctor | `dream doctor` | plugin + runtime check |
| Test | `dream test` | deterministic gates |
| Eval dry-run | `dream eval --dry-run` | preview, no scoring |
| Run | `dream run` | test → eval → decisions |
| Status | `dream status` | live pending counts |
| Scope | `dream scope` | in-scope pending list |
| Index | `dream index` | index summary |
| Which | `dream which` | resolved plugin CLI path |

---

## Agent contract

Agents must not screen-scrape the rendered frame. Instead:

1. Call `dream agent --json` to discover readiness and recommended next actions.
2. Call `dream capabilities --json` for the full command matrix.
3. Drive individual commands with `--json` (e.g. `dream run --json`).
4. Use `dream tui --json` to read the exact human menu model when mirroring the UI.

Exit codes: `0` ok · `1` runtime/plugin error · `2` usage error. Delegated plugin
commands propagate the plugin's own exit code.
