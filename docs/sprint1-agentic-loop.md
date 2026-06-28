# Agentic Loop Spec — Memory Trust Sprint 1

> **Status:** active execution spec for Sprint 1 (Memory Governance Core).
> **Mode:** no human in the loop · full access · async subagents · verify gate.
> **Sprint dates:** 2026-07-13 to 2026-07-26

## 1. Objective

Deliver Sprint 1 exit criteria:
- [x] Evidence + VerifierResult + CuratorDecision types (CHEF-1004)
- [x] schema_v4.sql migration (evidence, verifier_results, curator_decisions tables)
- [x] AgentMemory governance methods (propose, verify, curate, write_idempotent)
- [x] AgentMemoryStore governance CRUD methods
- [x] __init__.py exports for new types
- [x] 25 governance tests (types, state machine, lifecycle, idempotent writes)
- [ ] Deploy schema_v4.sql to staging (requires DB credentials)
- [ ] Wire governance pipeline to dashboard (read-only governance views)

## 2. Architecture

### State machine

```
proposed → reviewing → accepted | rejected | edited | deferred
deferred → reviewing
accepted → rolled_back
rejected → (terminal)
edited → (terminal)
rolled_back → (terminal)
```

### File domains

| File | Sprint 1 changes |
|------|-----------------|
| `types.py` | Evidence, EvidenceType, VerifierResult, VerifierStatus, CuratorDecision, CuratorState, CURATOR_VALID_TRANSITIONS |
| `store/migrations/schema_v4.sql` | evidence, verifier_results, curator_decisions tables + idempotency index |
| `agent_memory.py` | propose(), verify(), curate(), write_idempotent() |
| `store/postgres.py` | write_evidence, write_verifier_result, write_curator_decision, get_active_curator_decision, update_curator_decision, find_active_by_dedupe_key, curator_metrics |
| `__init__.py` | New type exports |
| `tests/test_governance.py` | 25 tests |

## 3. Remaining work

### Deploy migration
Apply `schema_v4.sql` to staging/production Postgres:
```bash
psql $DATABASE_URL -f python/src/dreaming_memory/store/migrations/schema_v4.sql
```

### Dashboard integration
Add read-only governance views to the dashboard:
- `/api/governance/proposed` — list memories in proposed state
- `/api/governance/metrics` — curator lifecycle metrics (acceptance rate, avg time)
- `/api/governance/{memory_id}` — evidence + verifier results + curator decisions

### Full pipeline test
Integration test covering propose → verify → curate → accept lifecycle with real Postgres.

## 4. Verification

Run `make check` to validate:
- Python: ruff lint + 125 tests
- Node: lint + tui/cli tests
- YAML: workflow validation
