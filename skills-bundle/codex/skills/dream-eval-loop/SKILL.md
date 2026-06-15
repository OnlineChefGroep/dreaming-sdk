---
name: dream-eval-loop
description: Unattended dream evaluation pipeline for Codex — deterministic tests, golden corpus eval, faithfulness scoring. Writes only eval/results/. Requires dreaming plugin CLI at ~/.cursor/plugins/local/dreaming/.
---

# dream-eval-loop (Codex / OpenAI)

Codex-compatible orchestrator. Install to `.agents/skills/dream-eval-loop/` and register in `00-skills` index.

## Trigger

```
Apply the dream-eval-loop skill to run one evaluation pass of the dreaming plugin.
```

## Shared orchestration

Follow the bundle shared docs (do not duplicate the loop here):

- `shared/orchestration-body.md`
- `shared/chain-reference.md`
- `shared/cli-contract.md`
- `shared/metrics-schema.md`

## CLI

```shell
cd ~/.cursor/plugins/local/dreaming
node cli/dream.mjs test --json
node cli/dream.mjs eval --corpus eval/golden-corpus --json
node cli/dream.mjs decisions --json
```

## Codex subagent mapping

| Step | `.agents/subagents/` or inline | Mode |
|------|-------------------------------|------|
| 1 | dream-evaluator | readonly |
| 2 | dream-judge | readonly; no soul.md |
| 5 | — | curator not used |

## Index registration

Add to `.agents/skills/00-skills/SKILL.md`:

`| dream-eval-loop | active | dream eval, faithfulness gate | Golden corpus eval orchestrator |`

## Unattended schedule

Codex has no Cursor Automation. Use:

- Host cron + Codex session with trigger prompt, or
- GitHub Actions calling `dream test` then agent step (Phase 2)

## Boundaries

Same as all platforms — see `shared/orchestration-body.md` guardrails.
