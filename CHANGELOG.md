# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Open-source governance: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  `CHANGELOG.md`, issue templates, pull request template, and `CODEOWNERS`.
- Continuous integration workflow (`.github/workflows/ci.yml`) running `ruff` + `pytest`
  for the Python package (Python 3.11 and 3.12) and syntax checks for the Node CLI.
- Root npm package `@onlinechefgroep/dream-cli` foundation (`package.json`, `bin/dream.js`).
- `AGENTS.md` documenting architectural boundaries for human and AI contributors.
- Python CLI `export` command (export session memory as Markdown) and `slack-report`
  command, plus a `SlackClient` integration and an extended `doctor` health check
  (Linear + Notion).
- Python unit tests covering the Slack integration and Markdown export rendering.
- `docs/agentic-loop-spec.md` describing the autonomous hardening run.
- Contributor ergonomics: `Makefile`, `.editorconfig`, and `docs/quickstart.md`.
- Maintainer and release documentation: `docs/maintainer-guide.md`,
  `docs/release-process.md`, and `docs/oss-readiness.md`.
- Supply-chain/security automation: Dependabot, CodeQL, Dependency Review, and release
  artifact build workflows.

### Changed

- Consolidated the foundation work from pull requests #2 and #3 into a single coherent
  state, with a richer README "Phases" table including status.
- `weekly-eval` workflow now performs real, fail-loud validation (Node syntax check,
  Python lint + tests) instead of printing a fake "simulation passed" message.
- CI now builds the Python package and validates the TypeScript cloud-runner wrapper.
- Python package metadata now includes public project URLs, keywords, and trove
  classifiers.

### Fixed

- **CI silent failure** — `weekly-eval.yml` no longer comments out its main command and
  reports green without doing work.
- **SDK recursion** — `sdk/run-dream-cloud.ts` now guards against infinitely spawning
  itself when `DREAM_PLUGIN_ROOT` points at the SDK repo.
- **CLI `export` crash** — the `export` command initializes its memory store before use
  (previously raised `NameError`).
- **CLI `doctor` crash** — the Notion health check uses `config.notion_api_key` instead
  of the non-existent `config.notion_token` (previously raised `AttributeError`).

## [0.1.0] - 2026-06-19

### Added

- Initial repository foundation: README, MIT license, architecture and operations docs.
- Automation prefill JSON (`automations/`) and the multi-agent skills bundle
  (`skills-bundle/`).
- Python "agent memory" extension (`python/`) backed by a Postgres single source of
  truth, with Linear and Notion integrations and an optional LanceDB semantic store
  (CHEF-308).

[Unreleased]: https://github.com/OnlineChefGroep/cursor-dreaming-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/OnlineChefGroep/cursor-dreaming-sdk/releases/tag/v0.1.0
