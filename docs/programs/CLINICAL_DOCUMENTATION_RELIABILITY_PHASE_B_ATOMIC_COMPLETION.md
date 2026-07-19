# Clinical Documentation Reliability — Phase B atomic completion

## Implemented contract

`POST /api/patient-journeys/{journey_id}/activities/{activity_id}/form/complete`

```json
{
  "data": { "complications": "Bez komplikacija." },
  "expected_instance_id": 17,
  "expected_revision_number": 4,
  "idempotency_key": "client-generated-uuid"
}
```

The endpoint locks the active instance, verifies its identity and revision, validates allowed keys and values, saves the exact submitted data, renders the summary, creates one revision, marks the form completed, writes one audit event and commits once.

The frontend does not issue a draft PATCH before completion. A clinician may enter required values and immediately choose **Dovrši obrazac**.

## Idempotency

The completed instance stores the completion key and SHA-256 hash of canonical submitted JSON.

- same key + same payload: returns the existing completed instance without a second revision or audit event;
- same key + different payload: HTTP 409 `idempotency_conflict`;
- different key after completion: rejected because the instance is no longer editable.

Migration `0053_form_reliability` adds both nullable columns with a paired-null check constraint. The migration is additive and reversible.

## Validation response

Validation failures return structured `fields` entries containing the internal key, Croatian label and clinician-facing message. The label, not the raw key, is the primary UI text. A failed completion performs no partial completion and creates no completion audit event.

## Evidence

- immediate completion persists `Bez komplikacija.` without prior draft save;
- missing required fields retain all submitted values and focus the invalid input;
- unknown keys fail before persistence;
- duplicate completion produces exactly one final revision;
- targeted PostgreSQL-backed backend tests pass;
- empty-database upgrade, downgrade one revision and re-upgrade pass.
