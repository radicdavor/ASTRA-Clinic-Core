# Program 1 Pilot Demo RC1 Push Tag Instructions

Release candidate: `program-1-pilot-demo-rc1`

## Pre-Push Checklist

- confirm branch is `main`
- confirm working tree is clean
- confirm local HEAD is the intended RC1 commit
- confirm `git log --oneline HEAD..origin/main` is empty
- confirm all required release validation checks passed
- confirm this is demo-only and synthetic-data-only
- confirm no production or real-data approval is implied

## Push Branch

```bash
git push origin main
```

## Create Annotated Tag

```bash
git tag -a program-1-pilot-demo-rc1 -m "Program 1 Pilot Demo RC1"
```

## Push Tag

```bash
git push origin program-1-pilot-demo-rc1
```

## Verify Remote Branch And Tag

```bash
git ls-remote --heads origin main
git ls-remote --tags origin program-1-pilot-demo-rc1
```

## Rollback Note

Do not delete or move the remote tag without explicit maintainer approval.

## Safety Warning

The tag does not mean production approval.

The tag does not mean real patient data approval.

The tag does not certify ASTRA Clinic Core as an EMR or medical device.
