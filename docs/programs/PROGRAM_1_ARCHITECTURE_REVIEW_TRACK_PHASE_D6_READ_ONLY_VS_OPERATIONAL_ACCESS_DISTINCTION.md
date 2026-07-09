# Program 1 Architecture Review Track Phase D6 - Read-Only vs Operational Access Distinction

Status: documentation-only conceptual distinction.

## Distinction

Read-only concept is documentation-only in Phase D. Operational access means connection to real systems or records.

Phase D does not permit:

- Operational access.
- Read-only runtime integration.
- Clinical use.
- Production-readiness claims.
- Database queries.
- EHR/EMR access.
- Patient record viewing.
- Real-data inspection.
- PHI/PII processing.

## Decision

Conceptual read-only reference is not runtime read access. Phase D does not authorize any connection to real systems, records, databases, audit logs, authorization logs, patient messages, appointments, EHR/EMR systems, production systems, or PHI/PII stores.
