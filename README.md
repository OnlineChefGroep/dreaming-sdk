# cursor-dreaming-sdk

**Integration kit for the Cursor dreaming plugin eval loop.**

Exportable orchestration patterns, automation templates, multi-agent skill bundles, and documentation so Cursor IDE, `@cursor/sdk`, OpenCode/Codex, Claude, Grok/Factory, and CI/webhook consumers can run the same dream-eval pipeline without forking the plugin.

> **Plugin required:** Install the dreaming plugin at `~/.cursor/plugins/local/dreaming/`. This repo does not replace it — it documents and wires how to call it.

**Full documentation:** see [`docs/`](./docs/) (mirrored from [utrecht-data-os `docs/ops/dreaming/`](https://github.com/OnlineChefGroep/utrecht-data-os/tree/main/docs/ops/dreaming)).

---

## What this repo is

| In this repo | In the plugin (local install) |
|--------------|-------------------------------|
| Automation prefill JSON | `cli/dream.mjs`, deterministic tests |
| Multi-agent skills bundle | Golden corpus, soul snapshot, schemas |
| Integration docs | Subagents (evaluator, judge, curator) |
| MIT LICENSE | Hooks, live `~/.cursor/dreaming/` state |

---

## Quick start

### 1. Verify plugin

```powershell
node $env:USERPROFILE\.cursor\plugins\local\dreaming\cli\dream.mjs test --json
```

### 2. Install eval skills (Codex example)

```powershell
.\skills-bundle\install-dream-skills.ps1 -Platform codex -Target C:\path\to\your-repo
```

Then prompt: **"Apply the dream-eval-loop skill to run one golden corpus evaluation pass."**

### 3. Cursor Automation (weekly eval)

1. Open Cursor → Automations → New.
2. Prefill from `automations/dream_eval_weekly.json` (or MCP `open_automation`).
3. Cron: Monday 09:00 — prompt applies `dream-eval-loop` skill.
4. Artifacts: `eval/results/<run_id>/metrics.json` + `summary.md`.

### 4. Cursor SDK (local)

```powershell
cd $env:USERPROFILE\.cursor\plugins\local\dreaming
$env:CURSOR_API_KEY = "cursor_..."
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
dream test        # deterministic gates (hard_fail stops eval)
dream eval        # prepare eval/results/<run_id>/
dream status      # pending session counts (live loop only)
dream scope       # in-scope pending list
dream decisions   # acceptance/regret from W1 log
dream index       # index summary
```

All commands support `--json`. Spec: [skills-bundle/shared/cli-contract.md](./skills-bundle/shared/cli-contract.md).

---

## Automations included

| File | Schedule | Purpose |
|------|----------|---------|
| `automations/dream_eval_weekly.json` | Mon 09:00 | Golden corpus eval, faithfulness gate |
| `automations/dream_nightly_dryrun.json` | Daily 00:00 | Dry-run if pending ≥ 5 |

---

## Metrics baseline

Each eval run writes canonical `metrics.json` (25 keys) — faithfulness, precision/recall, acceptance/regret, soul_version, gate results.

**Latest baseline:** run `2026-06-15T07-17-00Z`, faithfulness **0.63**. Known limitation: recurrence inflation on 3 items — see [docs/eval-quality.md](./docs/eval-quality.md).

---

## Repo layout

```text
cursor-dreaming-sdk/
├── README.md                 ← this file
├── LICENSE                   ← MIT
├── docs/
│   ├── README.md             ← system overview + architecture diagram
│   ├── architecture.md
│   ├── sdk-integration.md
│   ├── multi-agent.md
│   ├── eval-quality.md
│   └── operations.md
├── automations/
│   ├── dream_eval_weekly.json
│   └── dream_nightly_dryrun.json
└── skills-bundle/
    ├── install-dream-skills.ps1
    ├── install-dream-skills.sh
    ├── cursor/ · claude/ · codex/ · opencode/ · grok/
    └── shared/
```

---

## Phases

| Phase | Deliverable |
|-------|-------------|
| 0 | Docs + automation JSON + skills bundle (this repo) |
| 1 | npm `@onlinechefgroep/dream-cli` (CLI + schema validation) |
| 2 | GitHub Actions weekly run + Slack/Notion post |
| 3 | Webhook API (`POST /v1/dream/eval`) + optional MCP |

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
