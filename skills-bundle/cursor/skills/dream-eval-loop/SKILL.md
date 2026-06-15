---
name: dream-eval-loop
description: Agent-side orchestrator for the dream evaluation pipeline — runs deterministic tests, golden corpus eval, faithfulness scoring, and metrics tracking. Invocable from chat (/dream-eval), a Cursor Automation (weekly quality gate), or the SDK (sdk/run-dream-cloud.ts). Does NOT apply memory or mutate ~/.cursor/AGENTS.md.
disable-model-invocation: true
inherits: [dream-eval]
user: disabled
---

# dream-eval-loop (Cursor)

**Reference copy** — live install: `~/.cursor/skills/dream-eval-loop/SKILL.md`

Cursor-specific entry points: `/dream-eval`, Cursor Automation cron, `@cursor/sdk` via `sdk/run-dream-cloud.ts`.

## Shared orchestration

The full 6-step loop, guardrails, and experiment contract live in the bundle shared docs (relative to this repo):

- [Orchestration body](../../shared/orchestration-body.md)
- [Chain reference](../../shared/chain-reference.md)
- [CLI contract](../../shared/cli-contract.md)
- [Metrics schema](../../shared/metrics-schema.md)

Apply the shared orchestration body verbatim. This file adds only Cursor-specific wiring.

## Cursor entry points

| Surface | How |
|---------|-----|
| Chat | `/dream-eval` or "Apply the dream-eval-loop skill" |
| Automation | "Dream Eval — Weekly Quality Gate" (cron Monday 9:00) |
| SDK | `node --experimental-strip-types sdk/run-dream-cloud.ts` |
| CLI dry-run | `node cli/dream.mjs eval --dry-run --json` |

## Automation integration

Prefill payloads: `~/.cursor/skills/dream-eval-loop/automations.json`  
Open via MCP `cursor-app-control.open_automation` with `prefillWorkflowData`.

## Subagent delegation (Cursor Task)

| Step | Subagent | Mode |
|------|----------|------|
| 1 report | `dream-evaluator` | readonly |
| 2 score | `dream-judge` | readonly, no soul.md |
| 5 apply | — | curator **not used** in eval |

## Sync note

On release, diff this file against `~/.cursor/skills/dream-eval-loop/SKILL.md`. Cursor-only frontmatter (`disable-model-invocation`, `inherits`, `user`) must not be copied to other platforms.
