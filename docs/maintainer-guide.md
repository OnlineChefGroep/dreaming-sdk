# Maintainer guide

This guide documents the operating model for maintainers of `cursor-dreaming-sdk`.

## Repository contract

`cursor-dreaming-sdk` is an integration kit, not the runtime plugin. Keep that
boundary strict:

- Runtime plugin: `~/.cursor/plugins/local/dreaming/`
- Live state: `~/.cursor/dreaming/`
- This repo: docs, automation prefills, portable skills, thin wrappers, Python memory
  extension, CI/governance

Never accept PRs that vendor plugin internals, live state, raw transcripts, PII, or
secrets.

## Required checks before merge

Every merge should satisfy:

```bash
make check
```

This covers:

- Python dependency sync (`uv sync --extra dev`)
- Ruff lint
- Pytest suite
- Node syntax checks for the root CLI and TypeScript wrapper
- Workflow YAML parse check

GitHub also runs:

- CI matrix for Python 3.11 and 3.12
- CodeQL analysis for Python and JavaScript/TypeScript
- Dependency Review on pull requests
- Dependabot update proposals
- Weekly Dream Eval validation

## Review focus

Prioritize these risks in review:

1. **Boundary violations** - plugin source, live memory, or soul state copied into this
   repository.
2. **Eval mutation** - golden eval must not mutate live `~/.cursor/dreaming/`.
3. **Secret exposure** - API keys, DSNs, webhook URLs, transcripts, and PII must not be
   committed.
4. **Silent green failures** - CI/workflow steps must do real work or fail loudly.
5. **Schema/API drift** - CLI contracts must remain aligned with
   `skills-bundle/shared/cli-contract.md`.

## Automated dependency updates

Dependabot is configured for:

- GitHub Actions
- Root npm package
- Python package metadata under `python/`

For dependency PRs:

1. Check the changelog/release notes.
2. Confirm CI, CodeQL, and dependency review are green.
3. Run `make check` locally for non-trivial updates.

## Incident handling

If a secret or PII is committed:

1. Treat it as a security incident.
2. Rotate/revoke the exposed credential immediately.
3. Follow [../SECURITY.md](../SECURITY.md) for private reporting and disclosure.
4. Purge or rewrite history only with explicit maintainer coordination.

## Release readiness

Use [release-process.md](./release-process.md) for release steps. The `Release
Artifacts` workflow builds artifacts on tags and via manual dispatch, but publishing is
intentionally manual until package ownership and credentials are finalized.
