# Agentic Loop Spec — Memory Trust Sprint 0

> **Status:** active execution spec for Sprint 0 (Foundation Triage).
> **Mode:** no human in the loop · full access · async subagents · verify gate.
> **Sprint dates:** 2026-06-29 to 2026-07-12

## 1. Objective

Deliver all Sprint 0 exit criteria:
- [x] Naming, imports, URL consistency (CHEF-1000) — **code done (WIP)**
- [x] Eval artifact persistence round-trip (CHEF-1001) — **code done (WIP)**
- [x] Default secret gate patterns + CLI behavior (CHEF-1002) — **code done (WIP)**
- [x] CLI alias + MCP/package version sync (CHEF-1003) — **code done (WIP)**
- [ ] **Fix eval 0-score bug** — `_load_eval_report` fallback paths (root cause found)
- [ ] Commit WIP + fixes; verify Sprint 0 exit criteria

## 2. Roles

| Role | Responsibility |
|------|----------------|
| **Orchestrator** | Plans, dispatches, integrates, owns git, runs verify loop |
| **Builder A — Foundation** | `cli.py` fix + commit WIP + tests |
| **Builder B — Verify** | Runs tests/lint/gates, checks exit criteria, reports pass/fail |

## 3. Disjoint file domains

- Builder A → `dream-eval/src/dream_eval/cli.py`, `.github/workflows/`, `eval/`, `docs/`
- Builder B → read-only: tests, lint, gates, docs

## 4. Loop algorithm

```
1. plan()                         # this spec
2. commit_wip()                   # stage + commit 48 WIP files
3. dispatch(fix_eval_0score)      # fix cli.py fallback paths
4. loop:
    report = verify()             # tests, lint, gates, exit criteria
    if report.passed:
        break
    dispatch(fixers(report.failures))
5. final_report()                 # closing summary
```

## 5. Definition of done

- [x] All CHEF-1000/1001/1002/1003 code changes committed
- [ ] `_load_eval_report` fallback paths fixed in cli.py
- [ ] `_load_labels` fallback paths fixed in cli.py
- [ ] `python -m pytest dream-eval/tests/` passes
- [ ] `ruff check dream-eval/src/` passes
- [ ] `dream-eval run` produces `sessions_evaluated > 0` from repo root
- [ ] `dream-eval gates --text` scans with default patterns
- [ ] Fresh clone quickstart works (documented)
