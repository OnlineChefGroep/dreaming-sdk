# Agentic Loop Spec — Open-Source Hardening Run

> **Status:** active execution spec for the autonomous run that consolidates the
> open pull requests and brings `dreaming-sdk` to an open-source-ready state.
>
> **Mode:** no human in the loop · full access · multiple async subagents · 1 verify agent.

This document is the *prepared specification* the orchestrator follows. It is written
first (before any code changes) so the loop is deterministic, auditable, and resumable.

---

## 1. Objective

1. **Pick up the open PRs** (#2 *Improve and Expand SDK Foundation*, #3 *Initialize SDK
   Foundation and CI/CD Pipeline*) and consolidate their non-overlapping value into one
   coherent change, fixing every bug the automated reviewers (Sentry, kilo-code-bot)
   flagged.
2. **Harden the whole repository** so it is genuinely open-source ready: governance
   docs, contribution workflow, security policy, working CI, real (non-stubbed)
   automation, and a passing test + lint suite.

---

## 2. Roles in the loop

| Role | Type | Responsibility |
|------|------|----------------|
| **Orchestrator** | this agent | Plans, partitions work into disjoint file domains, dispatches subagents, integrates results, owns all git operations, runs the convergence loop. |
| **Builder A — Foundation** | async subagent | Consolidates PR #2/#3 foundation files and fixes their bugs. |
| **Builder B — Python** | async subagent | Hardens the `python/` package, adds the new CLI commands *correctly*, adds tests. |
| **Builder C — Governance** | async subagent | Adds open-source governance, templates, and CI. |
| **Verify agent** | async subagent | Independently re-runs tests/lint/build, checks the reviewer bugs are gone, and audits open-source readiness. Read-only w.r.t. intent; reports pass/fail with evidence. |

**Disjoint file domains** (guarantees no write conflicts during fan-out):

- Builder A → `AGENTS.md`, `package.json`, `bin/`, `sdk/`, `.github/workflows/weekly-eval.yml`, `README.md` (Phases/CI sections only).
- Builder B → `python/**` only.
- Builder C → `.github/ISSUE_TEMPLATE/**`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/workflows/ci.yml`, `.github/CODEOWNERS`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, `.gitignore`.

---

## 3. Reviewer bugs that MUST be fixed (acceptance gate)

| # | Source | File | Bug | Fix |
|---|--------|------|-----|-----|
| 1 | Sentry + kilo (HIGH/critical) | `.github/workflows/weekly-eval.yml` | Main eval command commented out → silent green failure. | Workflow must actually do meaningful, non-stubbed work (validate inputs/run real checks) and fail loudly when it cannot. |
| 2 | Sentry + kilo (MED/warn) | `sdk/run-dream-cloud.ts` | Self-spawn infinite recursion when `DREAM_PLUGIN_ROOT` points at the repo root. | Add a recursion guard env var **and** refuse to spawn a runner that resolves to this file. |
| 3 | Sentry (HIGH) | `python/.../cli.py` `export` | Uses `memory` before it is initialized → `NameError`. | Initialize the store before the `export` branch (or inside it). |
| 4 | Sentry (HIGH) | `python/.../cli.py` `_doctor` | References non-existent `config.notion_token` → `AttributeError`. | Use `config.notion_api_key` only. |

---

## 4. Loop algorithm

```
plan()                      # this spec
branch()                    # cursor/opensource-ready-agentic-loop-8422
dispatch([A, B, C])         # async, parallel, disjoint domains
integrate(results)          # orchestrator stages all changes
loop:
    report = verify()       # async verify agent
    if report.passed:
        break
    dispatch(fixers(report.failures))   # targeted re-dispatch
commit(); push(); open_pr()
```

- **No human in the loop:** the orchestrator never pauses for approval; it makes
  reasonable default decisions and records them here and in the PR body.
- **Full access:** subagents may read/write within their domain, install deps, and run
  the test/lint/build toolchain.
- **Convergence:** the loop exits only when the verify agent reports all gates green
  (tests, lint, workflow validity, reviewer bugs fixed, OSS files present).

---

## 5. Definition of done

- [ ] PR #2 + #3 value consolidated; all four reviewer bugs fixed.
- [ ] `python` test suite + `ruff` pass; new CLI commands covered by tests.
- [ ] CI workflow runs lint + tests for Python (and lints Node) on push/PR.
- [ ] Weekly-eval workflow does real, fail-loud work.
- [ ] Governance set present: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
      `CHANGELOG.md`, issue + PR templates, `CODEOWNERS`, `.gitignore`.
- [ ] README reflects the consolidated state; no stubbed "simulation" claims.
- [ ] Verify agent reports all gates green.
