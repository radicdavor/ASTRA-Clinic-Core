# Tagging v0.1-pilot

Use these steps only after the pilot release checklist passes and no P0/P1 pilot issues remain open.

```bash
git status
git pull
git log -1 --oneline
./scripts/validate_pilot_release.sh
```

Run required checks:

```bash
docker compose run --rm -e TEST_DATABASE_URL=postgresql+psycopg://astra:astra@db:5432/astra_clinic backend sh -lc "cd /app && python -m pytest -q"
cd frontend && npm run typecheck && npm run smoke && npm run build
```

Create and push the annotated prerelease tag:

```bash
git tag -a v0.1-pilot -m "ASTRA Clinic Core v0.1-pilot"
git push origin v0.1-pilot
```

GitHub release:

- Title: `ASTRA Clinic Core v0.1-pilot`
- Type: prerelease
- Notes source: `docs/releases/V0_1_PILOT_RELEASE_NOTES.md`

## Rollback

Remove a local tag:

```bash
git tag -d v0.1-pilot
```

Remove the remote tag:

```bash
git push origin :refs/tags/v0.1-pilot
```

Only remove a published tag if the release is unsafe, incorrectly tagged, or contains a P0/P1 blocker that was missed.
