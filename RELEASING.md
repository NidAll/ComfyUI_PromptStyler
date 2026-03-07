# Releasing

This repo uses Semantic Versioning and Release Please.

## Source Of Truth

Human-edited version source:

- `VERSION`

Mirrors and checks:

- `__init__.py` reads `VERSION` at runtime
- `.release-please-manifest.json` is synced from `VERSION` with `python tools/version_sync.py write`
- CI verifies version alignment with `python tools/version_sync.py check`

## Normal Maintainer Flow

1. Update `VERSION`.
2. Run `python tools/version_sync.py write`.
3. Run `python tools/validate_styles.py`.
4. Run `python tools/audit_styles.py`.
5. If packs changed, run `python tools/sync_legacy_styles.py` or `python tools/generate_style_packs.py`.
6. Update `CHANGELOG.md` and any user-facing docs that changed behavior.
7. Merge to `main`.
8. Release Please updates or opens the release PR.
9. Merge the release PR.

## CI

The repository CI job runs on pushes to `main` and on pull requests. It checks:

- version sync
- style validation
- style audit

## Manual Release

If automation is disabled:

1. Update `VERSION`.
2. Run `python tools/version_sync.py write`.
3. Update `CHANGELOG.md`.
4. Commit the release metadata.
5. Tag the commit:

```bash
git tag vX.Y.Z
git push --tags
```
