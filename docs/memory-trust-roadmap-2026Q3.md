# dreaming-sdk Memory Trust Layer Roadmap 2026Q3

Date: 2026-06-28 Europe/Amsterdam
Status: active PR roadmap, not yet merged
Repo: `OnlineChefGroep/dreaming-sdk`
Branch: `roadmap/memory-trust-2026q3`
PR: https://github.com/OnlineChefGroep/dreaming-sdk/pull/14
Notion working plan: https://app.notion.com/p/38cecd7f1c1a81ce93aded3fe39ce959
Linear project: https://linear.app/chefclawsheesh/project/dreaming-plugin-upgrade-and-eval-c8a9bc7d8d68

## Executive status

`dreaming-sdk` is no longer only a small alpha memory/eval repo. PR #14 has expanded into the foundation for a memory trust layer: governance models, schema migration, idempotent writes, external memory adapter contracts, workflow benchmarks, dashboard endpoints, docs, CI, and agent wiring.

The roadmap page was stale because it still described the work as mostly upcoming. Current reality:

- PR #14 is open, not draft, mergeable, and large: 11 commits, 84 changed files, about 4.5k additions.
- The original PR body said documentation-only; that is no longer true.
- Dependency Review is green.
- CodeRabbit status is green.
- CI is red.
- CodeQL is red.
- Linear project and issues still mostly show planned/Todo state, while GitHub already contains substantial implementation work.

Shipping rule: do not merge PR #14 until CI and CodeQL are green and the README/package naming residue is cleaned.

## Product direction

`dreaming-sdk` should be positioned as a memory trust layer, not as another generic memory engine.

```text
memory engines = Mem0 / Zep / LangMem / Cognee / Letta
dreaming-sdk = verify, score, block, curate, and persist trust state around memory
```

The project should own the trust boundary around agent memory:

- before a memory write: evidence, secret gates, verifier score, curator decision, dedupe key
- after a memory recall: source refs, stale-state checks, contradiction checks, trust metadata
- across runs: durable audit trail, reproducible eval artifacts, workflow benchmark results
- across backends: Postgres default plus adapters/sidecars for external memory engines

## Source-of-truth policy

Use the surfaces like this:

- GitHub: execution truth. Code, tests, CI, PR status, roadmap file.
- Notion: planning truth. Sprint plan, status board, decision log, human-readable handoff.
- Linear: issue tracker. Work slicing, priority, milestones, ownership.

If they disagree, prefer GitHub for implementation status, then sync Notion and Linear.

## Current implementation inventory

### Already implemented or substantially drafted in PR #14

- Public roadmap file: `docs/memory-trust-roadmap-2026Q3.md`.
- README/docs expansion for `dream-eval`, `dreaming-memory`, quickstart, operations, release process, agent memory, SDK integration, and multi-agent docs.
- `dream-eval` default secret gate patterns for common secrets/tokens/keys.
- `dream-eval` artifact persistence changes: `metrics.json`, `eval-report.json`, and `summary.md` path.
- Typed governance models: `Evidence`, `VerifierResult`, `CuratorDecision`, `CuratorState`, `VerifierStatus`, `EvidenceType`.
- `AgentMemory` governance facade: `propose()`, `verify()`, `curate()`, `write_idempotent()`.
- Postgres governance migration: `evidence`, `verifier_results`, `curator_decisions`, indexes, schema version 4.
- Memory engine adapter protocol split into `MemoryEngine` and `GovernanceEngine`.
- Mem0 adapter skeleton that documents sidecar governance pattern, but is not live.
- Benchmark package with schema, evaluator, CLI, and scenarios for GitHub PR review, Linear triage, Cloudflare change, Notion update, and memory write.
- Governance dashboard endpoints for proposed/reviewing memories, governance metrics, and governance detail per memory.
- Agent/skill wiring under `.mimocode`, `AGENTS.md`, skills bundle, and plugin metadata.

### Partial or risky

- README still contains stale `cursor-dreaming-sdk` badge/clone references. This keeps CHEF-1000 open.
- PR is not documentation-only anymore, so review scope must be treated as code + docs + CI.
- Linear issue states still show Todo/planned even though implementation exists in the PR branch.
- Mem0 adapter is a skeleton and explicitly raises `NotImplementedError` for live operations.
- Benchmark evaluator exists, but still needs stronger runner contracts, corpus validation, and CI artifact reporting.
- Dashboard exists, but should remain read-only until governance writes are fully tested.
- CodeQL failure is unresolved and must block merge.
- Python package pytest fails across Python 3.11, 3.12, and 3.13 for the `python` package job.

### Not implemented yet

- Full Zep/Graphiti, LangMem, and Cognee adapter proofs.
- Release-quality external memory engine sidecar store.
- End-to-end local benchmark runner against a real agent harness.
- Public alpha package release gate.
- Final acceptance report generated from CI/eval artifacts.
- Hosted dashboard/product packaging.

## CI and merge blockers

Current blocker stack:

1. Fix `python` package tests on Python 3.11, 3.12, and 3.13.
2. Fix CodeQL Python analysis.
3. Fix CodeQL JavaScript/TypeScript analysis.
4. Update PR body and review framing from docs-only to code + docs.
5. Remove stale repo naming from README/package metadata.
6. Re-run CI after the above; merge only when CI, CodeQL, and Dependency Review are green.

Known green areas:

- `dream-eval` lint/tests/build pass on Python 3.11, 3.12, and 3.13.
- Node CLI syntax/package checks pass.
- Dependency Review passes.
- CodeRabbit status passes.

## Sprint status map

### Sprint 0 — Foundation Triage

Dates: 2026-06-29 to 2026-07-12
Linear issues: CHEF-1000, CHEF-1001, CHEF-1002, CHEF-1003
Current status: partially implemented in PR #14; not mergeable yet.

Implemented or drafted:

- Default secret gate patterns exist.
- Eval artifact persistence is improved in `JsonFileBackend`.
- CLI/docs/package surfaces were expanded.
- CI workflows exist and expose real blockers.

Still required:

- Fix stale `cursor-dreaming-sdk` references.
- Prove fresh-clone quickstart.
- Fix failing `python` pytest matrix.
- Fix CodeQL.
- Add/verify CLI smoke path for `dream-eval`, MCP, and `dream-memory`.
- Confirm artifact round-trip consistency for JSON and Postgres.

Exit criteria:

- Fresh clone quickstart works exactly as documented.
- `dream-eval` artifacts save, load, and score consistently.
- Secret scanning is useful by default.
- CLI, MCP, package build, and smoke tests pass in CI.
- README package names, badges, repo URLs, and clone instructions are consistent.

### Sprint 1 — Memory Governance Core

Dates: 2026-07-13 to 2026-07-26
Linear issues: CHEF-1004, CHEF-1005, CHEF-1006
Current status: substantial first implementation exists in PR #14; still needs hardening.

Implemented or drafted:

- `Evidence`, `VerifierResult`, `CuratorDecision`, lifecycle states, and transition map.
- `AgentMemory.propose()`, `verify()`, `curate()`, `write_idempotent()`.
- Schema v4 governance tables.
- Unit tests for model instantiation, valid/invalid transitions, propose/verify/curate, and idempotent writes.
- Dashboard governance endpoints.

Still required:

- Confirm Postgres migration runs cleanly from existing schema versions.
- Add stricter evidence source hashing/span model if needed.
- Confirm idempotency is source-system safe, not only dedupe-key based.
- Add end-to-end storage test around evidence + verifier + curator lifecycle.
- Decide whether `edited` should be terminal or loop back into review after edit.

Exit criteria:

- Proposed memories can point to concrete evidence.
- Verifier decision is machine-readable and persisted.
- Curator lifecycle drives metrics.
- Re-ingestion does not duplicate active memory.
- Rollback and terminal states are tested.

### Sprint 2 — Backend Interop

Dates: 2026-07-27 to 2026-08-09
Linear issues: CHEF-1007, CHEF-1008, CHEF-1009
Current status: adapter contract exists; external adapters are proof-level only.

Implemented or drafted:

- `MemoryEngine` and `GovernanceEngine` protocols.
- Mem0 adapter skeleton with sidecar governance pattern.
- Docs describing external engine wrapping.

Still required:

- Add fake in-memory adapter conformance tests.
- Implement sidecar governance store pattern behind adapter contract.
- Add Zep/Graphiti-style and LangMem/Cognee-style documented shims or fixture adapters.
- Extend MCP tools for evidence validation, proposed-memory submission, curator decisions, and backend status.
- Keep vendor integrations optional and dependency-light.

Exit criteria:

- Postgres remains default.
- External engines can be wrapped by the trust layer.
- Adapter tests run without vendor accounts.
- MCP can score, check, propose, verify, decide, and report backend status.

### Sprint 3 — Workflow Benchmark

Dates: 2026-08-10 to 2026-08-23
Linear issues: CHEF-1010, CHEF-1011, CHEF-1012
Current status: benchmark skeleton exists and scenario coverage started.

Implemented or drafted:

- Benchmark schema v1.
- Evaluator with action, contains/not-contains, memory write, evidence ref, forbidden action/phrase/state checks.
- Scenario folders for GitHub PR review, Linear triage, Cloudflare change, Notion update, and memory write.

Still required:

- Add corpus validation command.
- Add benchmark report writer with per-scenario and aggregate outputs.
- Add mocked agent runner and fixture-based regression tests.
- Add stale-state and contradiction cases across all domains.
- Add CI artifact upload for benchmark reports.

Exit criteria:

- Benchmark corpus runs locally without external accounts.
- Each scenario includes expected facts, forbidden claims, evidence refs, and stale-state cases.
- Output reports per-scenario and aggregate failures.
- Benchmark result is usable as a release gate.

### Sprint 4 — Packaging Docs CI

Dates: 2026-08-24 to 2026-09-06
Linear issues: CHEF-1013, CHEF-1014, CHEF-1015
Current status: docs expanded, but public-alpha polish is not done.

Implemented or drafted:

- Docs folder has roadmap, quickstart, operations, release process, agent memory, SDK integration, and runbooks.
- README includes dual package framing for `dream-eval` and `dreaming-memory`.
- CI and CodeQL workflows exist.

Still required:

- Rewrite README around memory trust layer positioning rather than generic memory/eval package.
- Fix stale repo badges and clone URLs.
- Add migration guide from alpha API to governed memory API.
- Add release gates for package import, CLI smoke, MCP smoke, eval sample, and benchmark sample.
- Keep Notion/Linear/GitHub links accurate.

Exit criteria:

- README explains what this is and is not.
- CI blocks broken package, CLI, MCP, eval, and benchmark states.
- Repo docs link Notion and Linear planning.
- Public roadmap doc is accurate and non-misleading.

### Sprint 5 — Productization

Dates: 2026-09-07 to 2026-09-20
Linear issues: CHEF-1016, CHEF-1017, CHEF-1018
Current status: dashboard exists earlier than planned, but should remain alpha/read-only.

Implemented or drafted:

- FastAPI metrics dashboard with HTML, `/api/metrics`, and `/healthz`.
- Governance endpoints for proposed/reviewing, metrics, and memory detail.
- Operations docs and fleet deployment assets started.

Still required:

- Make dashboard explicitly read-only for alpha.
- Add operations runbook that a new agent/dev can execute.
- Add acceptance report template and generator.
- Define follow-up backlog and cut lines after Q3.
- Decide package split and external positioning before public push.

Exit criteria:

- Dashboard shows trust metrics from stored records.
- A new agent/dev can run the system from docs.
- Acceptance report can be generated from CI/eval artifacts.
- Follow-up scope is explicit.

## Linear sync requirements

Linear project currently remains planned/Todo relative to the work already in PR #14. After PR cleanup starts, sync issues like this:

- CHEF-1000: keep open until naming/README/package URL cleanup is done.
- CHEF-1001: move to In Progress only after round-trip tests are green.
- CHEF-1002: likely close after default secret gate tests and CLI behavior are verified.
- CHEF-1003: keep open until CLI/MCP smoke tests pass.
- CHEF-1004/CHEF-1005/CHEF-1006: move to In Progress when governance tests pass and migration is verified.
- CHEF-1007: move to In Progress after adapter conformance tests exist.
- CHEF-1008: keep Todo until external adapter proof is more than skeleton.
- CHEF-1009: keep Todo until MCP governance tools are implemented.
- CHEF-1010/CHEF-1011/CHEF-1012: move only when benchmark runner/reporting are CI-backed.
- CHEF-1013/CHEF-1014/CHEF-1015: keep open until public README and release gates are done.
- CHEF-1016/CHEF-1017/CHEF-1018: keep open until dashboard/runbook/acceptance report are release-shaped.

## Agent execution protocol

Use this order for next agentic loop:

1. Inspect failing `python` pytest job logs and reproduce locally.
2. Fix tests or implementation; do not silence tests without proof.
3. Fix CodeQL failures.
4. Remove stale repo/package naming from README/docs/package metadata.
5. Update PR body and labels to reflect code + docs scope.
6. Add missing smoke tests for CLI and MCP.
7. Add benchmark validation/report command if cheap; otherwise open as P3 follow-up.
8. Re-run CI.
9. Sync Linear issue states and Notion status after green PR state.

## Cut lines

Do now:

- CI and CodeQL green.
- Naming/URL consistency.
- Artifact persistence and default gates.
- Evidence, verifier, curator lifecycle.
- Idempotent memory records.
- Adapter contract and minimal conformance tests.
- Workflow benchmark skeleton with validation.

Do later:

- Heavy dashboard write UI.
- Hosted dashboard/product service.
- Full graph database.
- Model-specific judge layers.
- Live vendor adapter dependencies.

## Definition of done for Q3 alpha

By 2026-09-20, this roadmap is done only if:

- PRs are small enough to review and CI green.
- `dream-eval` and `dreaming-memory` can be installed from a clean environment.
- Eval artifacts round-trip through JSON and Postgres.
- Secret gates run by default and catch common tokens/keys.
- Governed memories carry evidence, verifier result, curator state, and dedupe metadata.
- External memory engines can be wrapped behind the trust layer without making them mandatory.
- Workflow benchmark runs locally without external accounts.
- README positions the project as a trust layer, not a generic memory engine.
- Notion, Linear, and GitHub agree on current status.
