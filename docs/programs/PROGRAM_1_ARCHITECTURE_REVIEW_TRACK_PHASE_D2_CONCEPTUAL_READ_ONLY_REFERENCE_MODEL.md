# Program 1 Architecture Review Track Phase D2 - Conceptual Read-Only Reference Model

Status: documentation-only conceptual reference model.

## Definition

Read-only is a future conceptual reference category only. It may be discussed only as documentation in Phase D.

## Must not create

- Runtime access.
- Database queries.
- EHR/EMR reads.
- Patient record viewing.
- Appointment record viewing.
- Production data inspection.
- PHI/PII access.
- Audit log inspection.
- Authorization event inspection.
- Patient message inspection.

## Decision

Phase D does not authorize read-only runtime access, operational access, real-data inspection, PHI/PII processing, database access, EHR/EMR access, patient record viewing, production data inspection, runtime audit logging, runtime auth/authz/RBAC, clinical deployment, production use, or go-live.
