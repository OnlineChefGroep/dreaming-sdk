# Open-source readiness checklist

This checklist is the repository's public readiness contract. It is intentionally
practical: every item maps to a file, workflow, or maintainer behavior in this repo.

## Governance

- [x] MIT license (`LICENSE`)
- [x] Contributing guide (`CONTRIBUTING.md`)
- [x] Code of Conduct (`CODE_OF_CONDUCT.md`)
- [x] Security policy (`SECURITY.md`)
- [x] Changelog (`CHANGELOG.md`)
- [x] Pull request template (`.github/PULL_REQUEST_TEMPLATE.md`)
- [x] Issue templates (`.github/ISSUE_TEMPLATE/`)
- [x] Code owners (`.github/CODEOWNERS`)

## Contributor experience

- [x] Quickstart (`docs/quickstart.md`)
- [x] Maintainer guide (`docs/maintainer-guide.md`)
- [x] Release process (`docs/release-process.md`)
- [x] One-command local gate (`make check`)
- [x] EditorConfig (`.editorconfig`)
- [x] Root `.gitignore` for Node, Python, env files, and dream artifacts

## Automation

- [x] CI for Python lint/tests and Node syntax checks (`.github/workflows/ci.yml`)
- [x] Weekly dream eval validation (`.github/workflows/weekly-eval.yml`)
- [x] CodeQL (`.github/workflows/codeql.yml`)
- [x] Dependency Review (`.github/workflows/dependency-review.yml`)
- [x] Dependabot (`.github/dependabot.yml`)
- [x] Release artifact build (`.github/workflows/release.yml`)

## Safety boundaries

- [x] `AGENTS.md` documents plugin/SDK boundaries
- [x] Soul isolation rule documented
- [x] Eval isolation rule documented
- [x] Never-commit list for secrets, PII, transcripts, and live memory
- [x] Recursion guard in `sdk/run-dream-cloud.ts`
- [x] Weekly eval performs fail-loud checks before optional plugin execution

## Package metadata

- [x] Root npm package metadata and executable mapping
- [x] Python package metadata, URLs, keywords, and classifiers
- [x] Release dry-run builds both package surfaces

## Remaining pre-publication decisions

These are intentionally left for maintainers before a first public release:

- Confirm the public support email addresses in `SECURITY.md` and `CODE_OF_CONDUCT.md`.
- Decide whether npm/PyPI publishing should use trusted publishing.
- Decide whether GitHub Discussions should be enabled for support questions.
- Confirm package namespace ownership for `@onlinechefgroep/dream-cli`.
