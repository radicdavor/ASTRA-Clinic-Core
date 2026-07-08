# Program 1 Phase I5 - Audit Retention Export Governance Review

## Current Audit Surfaces

- snapshot capture audit
- acknowledgment audit
- denied-read and sensitive-read guard patterns where implemented

## Deferred Audit Areas

- successful timeline read audit is deferred by default to avoid audit noise
- successful findings/open-question read audit remains policy-dependent
- review workflow audit remains documentation-only

## Governance Rules

- audit records are not Outcome Evidence
- audit export must be privacy-minimized
- full clinical text should not be exported unless explicitly approved
- audit retention policy must be reviewed before production
- denied/out-of-scope access may become a future security audit candidate

## Production Blockers

Retention periods, export ownership, data minimization, access to audit exports and incident review procedures must be approved before production or real data.

