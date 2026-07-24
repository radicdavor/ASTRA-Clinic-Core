# Repository consolidation status

Status captured: 24 July 2026
Repository: `radicdavor/ASTRA-Clinic-Core`

## Canonical branch stack

```text
main (00adb04)
+-- PR #3 feature/full-stack-production-validation (5850342)
    +-- PR #6 fix/pr3-scope-and-audit-blockers (29114fa)
    |   +-- PR #7 ux/information-architecture-simplification (current local head)
    +-- PR #4 feature/backup-restore-recovery (f4c8343)
        +-- recovery implementation still targets the pre-0066 schema and is currently conflicting
```

The UX branch is based directly on PR #6 and contains every PR #6 commit. It
does not contain the recovery commits from PR #4.

## Pull request inventory

| PR | Base | Head | State | Merge state | CI at recorded remote head | Dependency |
| --- | --- | --- | --- | --- | --- | --- |
| #3 Full-stack Production Validation and Lean Core Optimization | `main` | `feature/full-stack-production-validation` | Open draft | Mergeable | Green | Parent integration branch |
| #6 Close PR #3 authorization scope architecture | `feature/full-stack-production-validation` | `fix/pr3-scope-and-audit-blockers` | Open draft | Mergeable | Green | Must merge into PR #3 branch, never directly into `main` |
| #7 Simplify ASTRA role workflows and information architecture | `fix/pr3-scope-and-audit-blockers` | `ux/information-architecture-simplification` | Open draft | Mergeable | Green at `dea5ef5`; the current head requires fresh CI after publication | Stacked on PR #6 |
| #4 PostgreSQL Backup, Restore and Disaster Recovery | `feature/full-stack-production-validation` | `feature/backup-restore-recovery` | Open draft | Conflicting | Historical checks green | Must wait for PR #3 merge and a dedicated 0066 update |

GitHub currently records no formal review object on these pull requests. Prior
independent review conclusions remain historical evidence, not GitHub approval.

## Ancestry

Recorded left/right commit counts:

```text
feature/full-stack-production-validation...fix/pr3-scope-and-audit-blockers  0 / 30
fix/pr3-scope-and-audit-blockers...ux/information-architecture-simplification  0 / 29
feature/full-stack-production-validation...ux/information-architecture-simplification  0 / 59
```

There is no unexpected ancestry divergence. No rebase or force-push is needed.

## Schema and security baseline

The current security/UX stack has one expected Alembic head:

```text
0066_api_key_tenant_scope
```

PR #6 owns the additive security migrations `0064` through `0066`, including
tenant-scoped API keys, clinic/institution provenance, PHI-safe audit
projections, route registration and medical-category enforcement.

## Required integration order

1. Publish and revalidate the local UX head; keep PR #7 as a draft.
2. Record human-usability evidence honestly. Technical preflight is not human evidence.
3. Merge PR #6 into `feature/full-stack-production-validation` only after its
   reviewed head and current CI are reconfirmed.
4. Retarget PR #7 to `feature/full-stack-production-validation` only after step
   3, then verify the diff contains only UX/persona/usability work.
5. Integrate PR #7 only when its technical gate passes and the owner explicitly
   accepts the recorded human-usability status.
6. Run one complete integrated gate and adversarial review on the final PR #3 head.
7. Leave PR #3 unmerged until explicit owner authorization.
8. Leave PR #4 untouched until PR #3 is merged to `main`; then update recovery
   manifests, integrity projections and negative tests for schema `0066`.

## Current decision

Repository consolidation is in progress. Production use, real patient data and
the Clinical Document Engine remain unauthorized.
