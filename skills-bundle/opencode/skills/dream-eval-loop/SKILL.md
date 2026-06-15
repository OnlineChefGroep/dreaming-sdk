---
name: dream-eval-loop
description: Unattended dream evaluation pipeline for OpenCode — golden corpus eval, faithfulness scoring, metrics tracking. Plugin CLI required. Does not mutate live dreaming state.
---

# dream-eval-loop (OpenCode)

Install to `.opencode/skills/dream-eval-loop/SKILL.md`.

## Trigger

```
Apply the dream-eval-loop skill.
```

## Shared orchestration

- `shared/orchestration-body.md` — 6-step loop
- `shared/chain-reference.md` — handoffs
- `shared/cli-contract.md` — CLI JSON
- `shared/metrics-schema.md` — metrics.json keys

## CLI entry

Plugin root: `~/.cursor/plugins/local/dreaming`

```shell
node cli/dream.mjs test --json
node cli/dream.mjs eval --corpus eval/golden-corpus --json
node cli/dream.mjs decisions --json
```

## OpenCode scheduling

No built-in cron. Options:

1. System cron launches OpenCode with eval prompt
2. CI pipeline: deterministic `dream test` → OpenCode agent for evaluator/judge
3. Phase 3 MCP wrapper if shell unavailable

## Subagents

| Role | Eval | Notes |
|------|------|-------|
| dream-evaluator | yes | readonly |
| dream-judge | yes | never soul.md |
| dream-curator | no | live dream only |

## Install

```bash
cp -r docs/ops/dream-skill-bundle/opencode/skills/dream-eval-loop .opencode/skills/
```

Or symlink — see bundle `README.md`.
