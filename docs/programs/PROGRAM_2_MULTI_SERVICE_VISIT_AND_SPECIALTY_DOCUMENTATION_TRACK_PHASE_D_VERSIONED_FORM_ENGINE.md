# Program 2 Multi-Service Visit Track — Phase D

## Versioned clinician form engine

Status: runtime engine implemented; governed template editor UI remains pending.

The clinician engine is deliberately separate from patient-facing forms. Migration `0048_clinical_forms` adds definitions, immutable version identities, explicit service bindings, activity-scoped instances, and append-only edit revisions.

## Lifecycle

`draft → in_progress → completed → signed`

After signing, ordinary edits fail. A human must explicitly open an amendment; the signed instance is marked as amended and a new draft copies its data with `amended_from_instance_id` provenance. Completing a physical activity and signing its report remain separate actions.

## Controlled registry

Only the approved component registry is accepted. Form JSON cannot introduce executable components or arbitrary HTML. Every field requires a stable key, label, approved type, required marker, and controlled metadata. Duplicate keys and unknown submitted data keys fail validation.

## Deterministic binding

Resolution order is:

1. package-item version override;
2. clinic-specific service binding;
3. default service binding;
4. specialty and activity-kind default;
5. hard failure.

The resolver never examines a service name. It only accepts published versions and records the binding source and resolution time. Missing configuration produces a visible conflict and does not open a generic blank form.

## Human ownership and audit

- A clinician edits explicit structured data.
- Required fields are validated before completion.
- Signing requires a logged-in user with `clinical_forms.sign`.
- Resolve, edit, complete, sign and amend actions are audited.
- Each save creates a numbered revision snapshot.
- No AI output is committed or signed automatically.

## API

- `GET /api/clinical-forms/definitions`
- `POST /api/patient-journeys/{journey}/activities/{activity}/form/resolve`
- `GET|PATCH /api/patient-journeys/{journey}/activities/{activity}/form`
- `POST .../form/complete`
- `POST .../form/sign`
- `POST .../form/amend`

## Validation

Runtime tests cover missing-binding hard failure, deterministic default-service resolution, unknown-field rejection, required-field validation, completion, signing, signed-edit rejection, amendment provenance, duplicate keys and executable field rejection.

