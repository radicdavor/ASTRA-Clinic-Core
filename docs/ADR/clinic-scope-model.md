# ADR: Clinic-scoped authorization model

## Status

Accepted for Program 2 production-safety foundation.

## Decision

`Patient` is a person identity inside this ASTRA installation. A patient is not owned by exactly one clinic.

Clinic access to a patient is explicit through `PatientClinicAssociation(patient_id, clinic_id)`. One patient may be associated with multiple clinics.

Users receive clinic scope through `ClinicMembership(user_id, clinic_id)`. A user may work in multiple clinics, but deactivated memberships do not grant access.

For clinic-scoped clinical and financial data, authorization requires all three conditions:

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

The patient identity directory is intentionally broader: patient lookup during scheduling and exam entry may search the shared patient identity table to avoid duplicate entry and speed up form filling.

Patient appointment visibility is also broader for scheduling safety. Staff must be able to see that the same patient already has an appointment at another clinic so the patient cannot be booked in two places at the same time.

This broader scheduling visibility does not grant access to that patient's clinical documents, journeys, invoices, results, encounter notes, or other clinic-scoped context. When a clinic books or otherwise starts work with an existing patient identity, the association with that clinic must be created through a controlled service path.

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
