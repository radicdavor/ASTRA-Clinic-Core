# Program 1 Phase I11 - Source-Linking Integrity Governance

Source-linking is the central safety requirement for Program 1 clinical workflow surfaces.

## Covered Objects

- findings
- open questions
- extraction candidates
- review previews
- timeline events
- readiness snapshots and acknowledgments where they reference clinical context

## Required Display

- source object type/key where safe
- source type, label and reference
- limitations
- provenance
- safe fallback when source is incomplete

## No-Go Rule

Unlinked clinical truth is no-go. A source-linked record may be useful context, but it is not a final clinical decision, diagnosis, treatment plan, Task, Outcome Evidence or patient message.

## Future Repair Policy

Any future source repair/migration must be explicit, audited, reversible where practical and reviewed before production.

