# Documentation index

This index separates current authority from historical implementation evidence.
When documents disagree, verify the current code and configuration and use the
highest applicable current authority. A closure report proves only the commit,
scope and run it names; it does not automatically prove the current runtime or
production readiness.

## Canonical current state

These documents describe the maintained current state:

- [Architecture Bible](ASTRA_ARCHITECTURE_BIBLE.md) — highest architectural authority.
- [Current product state](CURRENT_PRODUCT_STATE.md) — current user-visible capabilities.
- [Current architecture](CURRENT_ARCHITECTURE.md) — current component and data boundaries.
- [Current operational limitations](CURRENT_OPERATIONAL_LIMITATIONS.md) — current known limitations and prohibitions.
- [Production-readiness backlog](PRODUCTION_READINESS_BACKLOG.md) — canonical operational and governance gaps.

## Architecture and ADRs

- [Architecture Bible compliance gate](V19_ARCHITECTURE_BIBLE_COMPLIANCE_GATE.md)
- [Design system](ASTRA_DESIGN_SYSTEM.md)
- [Workspace architecture](ASTRA_WORKSPACE_ARCHITECTURE.md)
- [`ADR/`](ADR/) — scoped architecture decisions.

Architecture proposals do not become authority until accepted by the owner.
Do not edit the Architecture Bible indirectly through a lower-level document.

## Security and privacy

- [Repository security policy](../SECURITY.md)
- [Security scope inventory](security-scope-inventory.md)
- [Current operational limitations](CURRENT_OPERATIONAL_LIMITATIONS.md)
- [`security/`](security/) — scoped security models and access matrices.

Security test success is technical evidence, not privacy, production or
real-patient-data authorization.

## Operations and recovery

- [Recovery contract](recovery-contract-0071.md)
- [Pilot runbook](PILOT_RUNBOOK.md)
- [Production-readiness backlog](PRODUCTION_READINESS_BACKLOG.md)

Current recovery evidence is synthetic. Production backup cadence, WAL/PITR,
off-site immutability, KMS ownership and measured production RPO/RTO remain
separate operational gates.

## Testing and release

- [Test strategy](test-strategy.md)
- [Release checklist](RELEASE_CHECKLIST.md)
- [Release evidence contract](release-evidence-contract.md)
- [Dependency management](dependency-management.md)

Exact-SHA evidence identifies what code ran. It never authorizes deployment,
production use or real patient data.

## Current program decisions

- [Readiness model](ASTRA_READINESS_MODEL.md)
- [Operational evidence loop](ASTRA_OPERATIONAL_EVIDENCE_LOOP.md)
- [Current product state](CURRENT_PRODUCT_STATE.md)
- [Current operational limitations](CURRENT_OPERATIONAL_LIMITATIONS.md)

Issue tracking is the source for active owner decisions and work status. Before
using a program document as current direction, compare it with open issues,
pull requests and the current canonical documents above.

## Historical implementation evidence

The following are retained for auditability but are not current-state authority:

- `programs/` phase plans, regression notes, matrices and closure reports;
- versioned `CODEX_MASTER_PROMPT*`, implementation reports and validation records;
- PR-specific remediation and security-review records;
- past release-candidate, pilot and track-closure documents;
- evidence documents that identify an older commit, workflow run or migration head.

Do not mass-delete or rewrite these records. Link to a historical document from
current documentation only when it explains a still-relevant decision or proof.

## Classification rule

Every new maintained document should fit one category above. If it describes a
temporary implementation phase or a single exact run, label it historical or
evidence-bound and include the relevant commit/run identity. Avoid declaring a
new document “canonical” when an existing current-state document already owns
that subject.
