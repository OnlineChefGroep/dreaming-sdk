# Release process

The repository currently ships two surfaces:

1. Root npm package foundation: `@onlinechefgroep/dream-cli`
2. Python package: `dreaming-memory`

Publishing remains manual until package ownership, trusted publishing, and credentials
are finalized. The automated release workflow builds artifacts but does not publish.

## Versioning

Use Semantic Versioning:

- `MAJOR` - incompatible CLI or Python API changes
- `MINOR` - backwards-compatible features
- `PATCH` - backwards-compatible fixes

Keep root `package.json` and `python/pyproject.toml` aligned when a release changes
both surfaces.

## Pre-release checklist

1. Confirm the changelog has an entry for the release.
2. Run the full local gate:

   ```bash
   make check
   make release-dry-run
   ```

3. Confirm GitHub Actions are green:
   - CI
   - CodeQL
   - Dependency Review (for PRs)
   - Weekly Dream Eval validation
4. Confirm there are no secrets or PII in the release diff.
5. Confirm `AGENTS.md` boundaries still match the shipped behavior.

## Build artifacts locally

```bash
make release-dry-run
```

This builds:

- Python wheel/sdist under `python/dist/`
- npm tarball preview via `npm pack --dry-run`

## Tagging

Use signed tags when available:

```bash
git tag -s v0.1.0 -m "v0.1.0"
git push origin v0.1.0
```

Pushing a `v*.*.*` tag triggers `.github/workflows/release.yml`, which rebuilds the
artifacts and uploads them to the workflow run.

## Publishing

Until trusted publishing is configured:

- Publish npm manually from a clean checkout after inspecting `npm pack --dry-run`.
- Publish Python manually after inspecting `python/dist/*`.
- Prefer GitHub Releases as the public release record and attach generated artifacts.

Do not add long-lived package registry tokens to repository secrets unless the security
model has been reviewed.
