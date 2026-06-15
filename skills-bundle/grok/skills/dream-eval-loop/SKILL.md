---
name: dream-eval-loop
description: Factory/Grok orchestrator for dream eval — golden corpus, faithfulness gate, metrics.json. Readonly eval; no curator. Plugin CLI at ~/.cursor/plugins/local/dreaming/.
---

# dream-eval-loop (Grok / Factory)

Factory-native path: `.factory/skills/dream-eval-loop/SKILL.md`  
Optional droid brief: `.factory/droids/dream-eval-loop.md` (copy skill header + CLI list).

## Trigger

```
Delegate to dream-eval-loop: run weekly golden corpus eval and write metrics.json + summary.md.
```

Or: "Apply the dream-eval-loop skill."

## Shared orchestration

- `shared/orchestration-body.md`
- `shared/chain-reference.md`
- `shared/cli-contract.md`
- `shared/metrics-schema.md`

## Factory droid pattern

Follow `.factory/droids/utrecht-pipeline.md` style. A `dream-eval-loop` droid should include:

1. **Readonly eval** — no AGENTS.md writes, no index reconcile during golden eval
2. **CLI commands** — verbatim from `shared/cli-contract.md`
3. **Subagent routing** — evaluator → judge; curator excluded
4. **soul.md rule** — judge and curator never read soul.md

## Subagent droids (optional)

| File | Eval | Live dream |
|------|------|------------|
| `.factory/droids/dream-evaluator.md` | yes | yes |
| `.factory/droids/dream-judge.md` | yes | no |
| `.factory/droids/dream-curator.md` | **no** | yes (write, user-approved) |

## CLI

```shell
cd ~/.cursor/plugins/local/dreaming
node cli/dream.mjs test --json
node cli/dream.mjs eval --json
node cli/dream.mjs decisions --json
```

## Index

Add row to `.factory/droids/README.md` under a new "Dream / continual learning" section.

## Do not wire

- `dreaming-stop` hook auto-trigger into droid (advisory only in Cursor)
- Live `status`/`scope` during golden eval (mutates index)
