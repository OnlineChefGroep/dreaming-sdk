# Changelog

## 0.2.0 (2026-06-26)

### Added
- **NLI claim verification** via Vectara HHEM-2.1-Open (`dream-eval[nli]`)
  - `verify_claim()` for single claim verification
  - `verify_content_nli()` for batch content matching
  - Automatic fallback to fuzzy matching if NLI extra not installed
- **Fuzzy content matching** with `fuzzy=True` parameter
  - Uses difflib SequenceMatcher (no LLM dependency)
  - Configurable threshold (default 0.85)
- **Async parallel scoring** via `score_transcripts_parallel()`
  - ThreadPoolExecutor-based parallelism
  - Preserves input order
- **Hypothesis property-based tests** for scoring invariants
  - Deterministic regression tests with `@example` decorator
  - Bounds checking for all scoring functions
- **MCP server** for Claude/Copilot/etc integration (`dream-eval-mcp`)
- **Agent Skills plugins** (`.claude-plugin`, `.codex-plugin`, `.cursor-plugin`)
- **Materialized views** for dashboard metrics (schema_v3.sql)

### Changed
- Pool tuning: `min_size=2, max_size=20, max_waiting=100`
- Faithfulness baseline target: 0.63 → 0.75

## 0.1.0 (2026-06-26)

### Added
- Initial release
- Scoring algorithms: precision, recall, faithfulness, recurrence calibration
- Deterministic gates: secret_leak, hash_determinism
- Backends: JsonFileBackend, PostgresBackend
- CLI: `dream-eval run/gates/score/list/show`
