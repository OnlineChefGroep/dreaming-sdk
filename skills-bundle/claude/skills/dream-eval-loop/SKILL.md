---
name: dream-eval-loop
description: Unattended dream evaluation pipeline — deterministic tests, golden corpus eval, faithfulness scoring, metrics.json. Does NOT mutate AGENTS.md or live dreaming state. Requires dreaming plugin at ~/.cursor/plugins/local/dreaming/.
---

# dream-eval-loop (Claude Code)

Orchestrator for the dreaming plugin eval pipeline on Claude Code. Shell access required for `node cli/dream.mjs`.

## Trigger

```
Apply the dream-eval-loop skill to run one golden corpus evaluation pass.
```

For live continual learning (interactive, with user approval before writes), use the plugin `dreaming` skill — not this skill.

## Shared orchestration

Read and follow:

- `docs/ops/dream-skill-bundle/shared/orchestration-body.md` (or bundle-relative `../../shared/orchestration-body.md` when installed from repo)
- `shared/chain-reference.md`
- `shared/cli-contract.md`
- `shared/metrics-schema.md`

## CLI (platform-agnostic)

```shell
cd ~/.cursor/plugins/local/dreaming
node cli/dream.mjs test --json
node cli/dream.mjs eval --corpus eval/golden-corpus --json
node cli/dream.mjs decisions --json
```

## Claude delegation

When Claude Code supports subagent/task delegation:

| Step | Role | Mode |
|------|------|------|
| 1 | dream-evaluator | readonly; isolated workspace |
| 2 | dream-judge | readonly; **never** read soul.md |
| 5 | — | dream-curator **not used** |

## Boundaries

- Writes only `eval/results/<run_id>/`
- Do not reconcile live dream index (`status`/`scope`/`index`) during golden eval
- `dream-curator` is for live `/dream` only, after explicit user approval

## Optional CLAUDE.md pointer

```markdown
Dream eval: apply skill `dream-eval-loop`. CLI: node ~/.cursor/plugins/local/dreaming/cli/dream.mjs test|eval|decisions --json
```

## MCP (Phase 3)

If shell unavailable, use MCP wrapper exposing `dream_test`, `dream_eval`, `dream_decisions` (read-only).
