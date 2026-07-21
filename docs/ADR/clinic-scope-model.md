# ADR: Clinic-scoped authorization model

## Status

Accepted for Program 2 production-safety foundation.

## Decision

`Patient` is a person identity inside this ASTRA installation. A patient is not owned by exactly one clinic.

Clinic access to a patient is explicit through `PatientClinicAssociation(patient_id, clinic_id)`. One patient may be associated with multiple clinics.

Users receive clinic scope through `ClinicMembership(user_id, clinic_id)`. A user may work in multiple clinics, but deactivated memberships do not grant access.

For clinic-scoped operational and financial data, authorization requires all three conditions:

1. the required permission;
2. an active membership in the selected clinic;
3. the object belongs to the active clinic, either directly or through its scoped parent.

The backend is the authority. A frontend-selected clinic or `X-Clinic-Id` header is only a requested context and is validated on every request.

## Active clinic rule

- If a user has no active clinic membership, clinic-scoped routes return `403`.
- If a user has one active clinic membership, the backend may use it automatically.
- If a user has multiple active clinic memberships, the request must include an explicit active clinic selection, currently via `X-Clinic-Id`.
- A clinic ID outside the user's active memberships is rejected with `403`.

## System administrator rule

`system.admin` is a system permission for administration. It is not a global PHI access grant.

A system administrator can manage system configuration and memberships when the matching administrative permission allows it, but still needs explicit clinic membership for normal clinical data access. No unaudited break-glass access is introduced in this phase.

## Operational object ownership

Aggregate clinical and financial objects belong to one clinic. The current additive foundation stores `clinic_id` on:

- `Appointment`
- `PatientJourney`
- `JourneyEncounter`
- `ClinicalDocument`
- `Invoice`

`JourneyActivity` already carries clinic context for activity-level scheduling and dashboard queries. Child records should derive clinic scope through their parent unless a direct aggregate root scope is required.

## Cross-clinic behavior

Direct object access across clinics should return `404` for object reads when possible, so the API does not reveal whether the object exists in another clinic.

Clinical, scheduling, document, billing, and dashboard list/search endpoints must return only data from the active clinic.

## Institution-wide clinical read

Accepted model name:

```text
Institution-wide clinical read with clinic-scoped operations and author-controlled writes
```

Clinical reading is intentionally broader than operational clinic scope. Medical staff inside the same institution may read clinical records created in any clinic, location, or specialty of that institution when all conditions are true:

1. the actor is authenticated as a user;
2. the actor has an active `ClinicMembership` in at least one clinic in the same institution;
3. the actor role has `professional_category = medical_staff`;
4. the actor has `clinical.documents.read_institution`;
5. the document is marked as clinical record material;
6. the document/patient belongs to the same institution.

This permits continuity of care: a nurse in Clinic A may read a gastroenterology report from Clinic B of the same institution, and a physician may read nursing documentation when needed for care.

This does not grant access to invoices, payments, discounts, commercial notes, HR data, system configuration, or clinic-local operational dashboards.

Implementation note: Module 3 introduces a real `Institution` aggregate and `Clinic.institution_id`. The previous additive `Clinic.institution_key` remains only as a compatibility/backfill key for legacy local and synthetic data. New institution-aware policies should use `Institution -> Clinic -> document/patient` first and fall back to `institution_key` only where older fixtures have not yet been migrated.

## Author-controlled clinical writes

Institution-wide read is not edit permission. Standard draft editing is restricted to the document author through `author_user_id` and `clinical.documents.edit_own_draft`.

Signed clinical documents are immutable. Standard `PATCH`/`PUT` paths must reject signed documents. Corrections are recorded as separate addenda with:

- their own ID;
- `original_document_id`;
- `author_user_id`;
- timestamp;
- reason;
- content;
- status/signature state;
- audit event.

The original document remains unchanged and readable.

## Patient identity and scheduling visibility

The patient identity directory is intentionally broader: patient lookup during scheduling and exam entry may search the shared patient identity table to avoid duplicate entry and speed up form filling.

Patient appointment visibility is also broader for scheduling safety. Staff must be able to see that the same patient already has an appointment at another clinic so the patient cannot be booked in two places at the same time.

This broader scheduling visibility does not grant access to that patient's clinical documents, journeys, invoices, results, encounter notes, or other clinic-scoped context. When a clinic books or otherwise starts work with an existing patient identity, the association with that clinic must be created through a controlled service path.

## Same-patient scheduling concurrency

Patient-time conflict checks are intentionally global to the patient identity, not limited to the active clinic. A patient can be visible for booking in multiple clinics, but cannot physically attend overlapping appointments in different rooms or clinics.

PostgreSQL scheduling writes acquire a transaction-scoped advisory lock keyed by patient ID before checking for overlapping blocking appointments. The lock serializes create and update attempts for the same patient across concurrent database transactions, so the conflict query and subsequent insert or update are evaluated as one critical section. The lock is released automatically on commit or rollback.

SQLite local tests no-op this advisory lock because SQLite has no equivalent primitive. The PostgreSQL integration suite contains the authoritative regression coverage for concurrent same-patient booking.

## `rescheduled` appointment semantics

The current appointment model has a `rescheduled` status, but it does not store a replacement-link such as `rescheduled_from_id`, nor a separate old-slot/new-slot lifecycle. In the current implementation the record still carries the operative date, time, provider, room, patient, and clinic.

For that reason, `rescheduled` remains a patient-time blocking status in scheduling, reception slot search, and overlap validation. Treating it as a non-blocking historical slot would be unsafe without an explicit replacement model and migration path, because the system could then double-book a patient into the same physical time window.

If ASTRA later introduces a true rescheduling model, the safer shape is:

- old appointment: terminal, non-blocking historical status with a reference to the replacement appointment;
- replacement appointment: active blocking status such as `scheduled` or `confirmed`;
- audit/event link preserving who moved the appointment, when, and why.

## Backfill rule

Migration `0057_clinic_scope_foundation` is additive and backfills only from unambiguous existing relationships:

- appointment scope from room clinic;
- journey scope from appointment clinic;
- encounter, document, and invoice scope from their journey or appointment where available;
- patient-clinic associations from scoped appointments and journeys.

The migration does not assign arbitrary default clinic IDs to ambiguous clinical data.

## Local use

Seed data creates demo clinic memberships for seeded users. For multi-clinic users, send:

```text
X-Clinic-Id: <clinic id>
```

The server validates the selected clinic against `ClinicMembership` before returning clinic-scoped data.
