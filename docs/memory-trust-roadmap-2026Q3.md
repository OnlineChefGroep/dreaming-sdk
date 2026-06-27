# dreaming-sdk Memory Trust Layer Roadmap 2026Q3

Date: 2026-06-27 Europe/Amsterdam

## References

- Notion working plan: https://app.notion.com/p/38cecd7f1c1a81ce93aded3fe39ce959
- Linear project: https://linear.app/chefclawsheesh/project/dreaming-plugin-upgrade-and-eval-c8a9bc7d8d68
- Linear document: https://linear.app/chefclawsheesh/document/dreaming-sdk-memory-trust-layer-roadmap-2026q3-1df246c442ae

## Direction

`dreaming-sdk` should be positioned as a memory trust layer, not as another generic memory engine.

```text
memory engines = Mem0 / Zep / LangMem / Cognee / Letta
dreaming-sdk = verify, score, block, curate, and persist trust state around memory
```

The project should own the trust boundary around agent memory:

- before a memory write: evidence, secret gates, verifier score, curator decision
- after a memory recall: source refs, stale-state checks, contradiction checks, trust metadata
- across runs: durable audit trail, reproducible eval artifacts, workflow benchmark results

## Current assessment

### Strengths

- Small readable Python codebase.
- Useful faithfulness scorer and deterministic gates.
- Postgres single source of truth is a good default.
- MCP exposure is the right integration surface for multiple agents.
- Existing tests around scoring and property bounds are good for alpha.

### Weaknesses

- Naming and docs still mix old/new package names.
- Eval artifact persistence does not round-trip cleanly.
- Secret gate skips without configured patterns.
- Linear/Notion ingestion can create duplicates.
- No typed evidence model or curator lifecycle yet.
- Market positioning is weak if framed as generic memory.

## Phase map

| Phase | Goal | Sprint |
|---|---|---|
| P0 Trust Foundation | Make current SDK consistent, safe, and testable | Sprint 0 |
| P1 Memory Governance Core | Evidence, verifier result, curator lifecycle, idempotency | Sprint 1 |
| P2 Backend Interop | Trust layer around other memory engines | Sprint 2 |
| P3 Workflow Benchmark | Evaluate agent workflows, not only chat recall | Sprint 3 |
| P4 Docs and CI | Package, docs, examples, release gates | Sprint 4 |
| P5 Productization | Dashboard, runbook, acceptance report, follow-up backlog | Sprint 5 |

## Sprint 0 — Foundation Triage

Dates: 2026-06-29 to 2026-07-12

Goal: remove blockers before adding architecture.

Linear issues:

- CHEF-1000 — Fix naming, package imports, and repo URL consistency.
- CHEF-1001 — Fix eval artifact persistence contract.
- CHEF-1002 — Add default secret gate patterns and CLI behavior.
- CHEF-1003 — Align CLI alias handling and MCP/package versions.

Exit criteria:

- Fresh clone quickstart works.
- `dream-eval` artifacts save, load, and score consistently.
- `dream-eval gates --text` performs useful scanning by default.
- CLI and MCP smoke tests run in CI.

## Sprint 1 — Memory Governance Core

Dates: 2026-07-13 to 2026-07-26

Goal: make memory trust state explicit.

Linear issues:

- CHEF-1004 — Add evidence source and verifier result models.
- CHEF-1005 — Implement curator decision state machine.
- CHEF-1006 — Add idempotent memory writes and external reference constraints.

Exit criteria:

- Proposed memories can point to evidence.
- Verifier decision is machine-readable.
- Curator lifecycle drives metrics.
- Re-ingestion does not duplicate active memory.

## Sprint 2 — Backend Interop

Dates: 2026-07-27 to 2026-08-09

Goal: separate storage/retrieval from trust/governance.

Linear issues:

- CHEF-1007 — Define memory engine adapter contract v1.
- CHEF-1008 — Build external memory engine adapter proofs.
- CHEF-1009 — Extend MCP tools for evidence and governance workflows.

Exit criteria:

- Postgres remains default.
- External engines can be wrapped by the trust layer.
- Adapters have fixture-backed tests.
- MCP can score, check, propose, and decide memory items.

## Sprint 3 — Workflow Benchmark

Dates: 2026-08-10 to 2026-08-23

Goal: evaluate real agent work, not only conversation recall.

Linear issues:

- CHEF-1010 — Design agent workflow benchmark schema and corpus format.
- CHEF-1011 — Add GitHub PR review and Linear triage benchmark scenarios.
- CHEF-1012 — Add Cloudflare change and Notion project update benchmark scenarios.

Exit criteria:

- Benchmark corpus runs locally without external accounts.
- Scenarios include expected facts, forbidden claims, evidence refs, and stale-state cases.
- Output reports per-scenario and aggregate failures.

## Sprint 4 — Packaging Docs CI

Dates: 2026-08-24 to 2026-09-06

Goal: make it explainable and safely releasable.

Linear issues:

- CHEF-1013 — Rewrite public README around memory trust layer positioning.
- CHEF-1014 — Add CI release gates for package, CLI, MCP, and eval sample.
- CHEF-1015 — Add migration guide and public roadmap doc.

Exit criteria:

- README explains what this is and is not.
- CI blocks broken package/CLI/MCP/eval states.
- Repo docs link Notion and Linear planning.

## Sprint 5 — Productization

Dates: 2026-09-07 to 2026-09-20

Goal: close alpha into usable project shape.

Linear issues:

- CHEF-1016 — Build trust metrics dashboard view.
- CHEF-1017 — Write operations runbook and acceptance report.
- CHEF-1018 — Define follow-up backlog and positioning cut lines.

Exit criteria:

- Dashboard shows trust metrics from stored records.
- A new agent/dev can run the system from docs.
- Acceptance report can be generated from CI/eval artifacts.
- Follow-up scope is explicit.

## Cut lines

Do now:

- Artifact persistence and default gates.
- Evidence and curator lifecycle.
- Idempotent memory records.
- Adapter contracts and workflow benchmark.

Do later:

- Heavy dashboard write UI.
- Full graph database.
- Model-specific judge layers.
- Hosted packaging.

## Immediate GitHub work

Start with Sprint 0. The first PRs should be small and mechanical:

1. naming/import/URL consistency
2. eval artifact persistence round-trip
3. default secret gate patterns
4. CLI alias and MCP version sync

Do not add backend adapters or benchmark work until the P0 fixes are merged.
