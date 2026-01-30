# Releasing

This repo uses **Semantic Versioning** and **Release Please** to keep releases organized.

## Normal Release Flow (recommended)

1. Merge changes into `main`.
2. The `release-please` workflow opens/updates a **Release PR** that:
   - bumps the version
   - updates `CHANGELOG.md`
3. Merge the Release PR.
4. Release Please creates a Git tag (e.g. `v0.2.0`) and a GitHub Release.

## Manual Release (if automation is disabled)

1. Update `__init__.py` `__version__` and `VERSION` to the new version.
2. Add notes under `CHANGELOG.md` and move them into a new version section.
3. Commit with a message like: `chore(release): vX.Y.Z`
4. Tag and push:

```bash
git tag vX.Y.Z
git push --tags
```

