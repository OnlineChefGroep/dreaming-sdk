# dreaming-sdk

[![CI](https://github.com/OnlineChefGroep/dreaming-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/OnlineChefGroep/dreaming-sdk/actions/workflows/ci.yml)
[![CodeQL](https://github.com/OnlineChefGroep/dreaming-sdk/actions/workflows/codeql.yml/badge.svg)](https://github.com/OnlineChefGroep/dreaming-sdk/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![PyPI dream-eval](https://img.shields.io/pypi/v/dream-eval.svg)](https://pypi.org/project/dream-eval/)
[![PyPI dreaming-memory](https://img.shields.io/pypi/v/dreaming-memory.svg)](https://pypi.org/project/dreaming-memory/)

**Integration kit for the Cursor dreaming plugin eval loop.**

Exportable orchestration patterns, automation templates, multi-agent skill bundles, and documentation so Cursor IDE, `@cursor/sdk`, OpenCode/Codex, Claude, Grok/Factory, and CI/webhook consumers can run the same dream-eval pipeline without forking the plugin.

> **Plugin required for plugin-backed commands:** Install the dreaming plugin at `~/.cursor/plugins/local/dreaming/`. This repo does not replace it — it documents and wires how to call it. The standalone Python packages can run without the Cursor plugin where their inputs are committed or passed explicitly.

**Full documentation:** see [`docs/`](./docs/) (mirrored from [utrecht-data-os `docs/ops/dreaming/`](https://github.com/OnlineChefGroep/utrecht-data-os/tree/main/docs/ops/dreaming)).

**Contributors:** start with [CONTRIBUTING.md](./CONTRIBUTING.md), then run `make check` before opening a PR.

---

## What this repo is

| In this repo | In the plugin (local install) |
|--------------|-------------------------------|
| **`dream-eval/`** — standalone faithfulness scoring and gates | `cli/dream.mjs`, deterministic plugin tests |
| Automation prefill JSON | Golden corpus, soul snapshot, schemas |
| Multi-agent skills bundle | Subagents (evaluator, judge, curator) |
| Integration docs | Hooks, live `~/.cursor/dreaming/` state |
| MIT LICENSE | |

---

## Quick start

### 1. Verify plugin

```bash
node bin/dream.js doctor
```

The CLI auto-detects the plugin at `~/.cursor/plugins/local/dreaming/`. If present, it reports the plugin root and version; if absent, it falls back to local TUI/agent mode.

### 2. Run the TUI (interactive)

```bash
node bin/dream.js tui
```

Use arrow keys or `j`/`k` to navigate, `/` to fuzzy-filter, `Enter` to run a command.

### 3. Install eval skills (Codex example)

```powershell
.\skills-bundle\install-dream-skills.ps1 -Platform codex -Target C:\path\to\your-repo
```

Then prompt: **"Apply the dream-eval-loop skill to run one golden corpus evaluation pass."**

### 4. Cursor Automation (weekly eval)

1. Open Cursor → Automations → New.
2. Prefill from `automations/dream_eval_weekly.json` (or MCP `open_automation`).
3. Cron: Monday 09:00 — prompt applies `dream-eval-loop` skill.
4. Artifacts: `eval/results/<run_id>/metrics.json` + `summary.md`.

### 5. Cursor SDK (cloud)

```bash
export CURSOR_API_KEY="cursor_..."
node --experimental-strip-types sdk/run-dream-cloud.ts
```

Cloud mode requires committed eval inputs in the target repo — see [docs/sdk-integration.md](./docs/sdk-integration.md).

---

## Multi-agent install paths

| Platform | Path | Install flag |
|----------|------|--------------|
| Cursor | `~/.cursor/skills/dream-eval-loop/` | `-Platform cursor -Global` |
| Claude | `.claude/skills/dream-eval-loop/` | `-Platform claude` |
| Codex | `.agents/skills/dream-eval-loop/` | `-Platform codex` |
| OpenCode | `.opencode/skills/dream-eval-loop/` | `-Platform opencode` |
| Grok/Factory | `.factory/skills/dream-eval-loop/` | `-Platform grok` |

Details: [docs/multi-agent.md](./docs/multi-agent.md) · [skills-bundle/README.md](./skills-bundle/README.md)

---

## CLI surface

```text
dream doctor        # inspect plugin and runtime
dream tui           # interactive terminal (human mode)
dream agent --json  # machine-readable agent envelope
dream run           # test → eval → decisions flow
dream test          # deterministic gates (hard_fail stops eval)
dream eval          # prepare eval/results/<run_id>/
dream status        # pending session counts (live loop only)
dream scope         # in-scope pending list
dream decisions     # acceptance/regret from W1 log
dream index         # index summary
dream cloud         # run SDK cloud wrapper
```

All commands support `--json` where applicable. Spec: [skills-bundle/shared/cli-contract.md](./skills-bundle/shared/cli-contract.md).

---

## Automations included

| File | Schedule | Purpose |
|------|----------|---------|
| `automations/dream_eval_weekly.json` | Mon 09:00 | Golden corpus eval, faithfulness gate |
| `automations/dream_nightly_dryrun.json` | Daily 00:00 | Dry-run if pending ≥ 5 |

---

## Open-source operations

| Area | File |
|------|------|
| Contributor quickstart | [docs/quickstart.md](./docs/quickstart.md) |
| Maintainer guide | [docs/maintainer-guide.md](./docs/maintainer-guide.md) |
| Release process | [docs/release-process.md](./docs/release-process.md) |
| OSS readiness checklist | [docs/oss-readiness.md](./docs/oss-readiness.md) |
| Security policy | [SECURITY.md](./SECURITY.md) |
| Contribution guide | [CONTRIBUTING.md](./CONTRIBUTING.md) |

Local quality gate:

```bash
make check
```

---

## Metrics baseline

Each eval run writes canonical `metrics.json` — faithfulness, precision/recall, acceptance/regret, soul_version, gate results.

**Latest baseline:** run `2026-06-15T07-17-00Z`, faithfulness **0.63**. **Target:** **0.75** — see [docs/eval-quality.md](./docs/eval-quality.md).

**dream-eval package:** `pip install dream-eval` — standalone scoring + gates, works with any memory backend.

---

## Repo layout

```text
dreaming-sdk/
├── README.md                 ← this file
├── LICENSE                   ← MIT
├── CONTRIBUTING.md           ← contributor guide
├── SECURITY.md               ← vulnerability reporting
├── CODE_OF_CONDUCT.md        ← community standards
├── docs/
│   ├── architecture.md
│   ├── agent-memory.md
│   ├── sdk-integration.md
│   ├── multi-agent.md
│   ├── eval-quality.md
│   └── operations.md
├── dream-eval/               ← standalone faithfulness evaluation framework
│   ├── src/dream_eval/       ← scoring, gates, backends, CLI, MCP server
│   ├── tests/
│   ├── .claude-plugin/
│   ├── .codex-plugin/
│   └── .cursor-plugin/
├── python/                   ← agent memory extension (Postgres + Linear/Notion)
│   ├── src/dreaming_memory/
│   ├── examples/
│   ├── deploy/oci/
│   └── tests/
├── automations/
│   ├── dream_eval_weekly.json
│   └── dream_nightly_dryrun.json
├── .github/
│   ├── workflows/            ← CI + release
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
└── skills-bundle/
    ├── install-dream-skills.ps1
    ├── install-dream-skills.sh
    ├── cursor/ · claude/ · codex/ · opencode/ · grok/
    └── shared/
```

---

## Phases

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 0 | Docs + automation JSON + skills bundle | ✅ Done |
| 0.5 | **Agent memory** (`python/`) — Postgres SSOT, Linear/Notion, optional LanceDB — [docs/agent-memory.md](./docs/agent-memory.md) | ✅ Done |
| 0.75 | **dream-eval** (`dream-eval/`) — standalone faithfulness scoring, gates, MCP server, Agent Skills plugins | 🟡 Beta |
| 1 | **npm `@onlinechefgroep/dream-cli`** — unified CLI + schema validation | 🟡 Beta |
| 2 | **GitHub Actions** — weekly golden evaluation + Slack/Notion reporting | 🟡 Beta |
| 3 | **Webhook API** — `POST /v1/dream/eval` + orchestration via MCP | 📅 Planned |
| 4 | **Soul Evolution** — automatic `soul.md` refinement based on acceptance rates | 📅 Planned |
| 5 | **Fleet Orchestration** — centralized dream-eval across multiple agent nodes | 📅 Planned |

CI runs lint + tests on every push/PR (workflow [`.github/workflows/ci.yml`](./.github/workflows/ci.yml)); the weekly golden eval runs via [`.github/workflows/weekly-eval.yml`](./.github/workflows/weekly-eval.yml) and fails when the plugin-backed cloud path cannot be proven.

---

## Paths & safety

- **Global state:** `~/.cursor/dreaming/` — index, decision log, dream reports
- **Plugin:** `~/.cursor/plugins/local/dreaming/` — CLI, eval corpus, schemas
- **Eval output:** `eval/results/<run_id>/` only — never mutates live memory

Do not commit secrets, PII transcripts, or live decision logs.

---

## Organization

Maintained by [OnlineChefGroep](https://github.com/OnlineChefGroep).

## License

MIT — see [LICENSE](./LICENSE).
