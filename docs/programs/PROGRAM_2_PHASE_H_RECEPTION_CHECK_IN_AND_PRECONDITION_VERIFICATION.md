# Program 2 — Phase H: Reception Check-In and Precondition Verification

## Status

Phase H implements a structured check-in aggregate and permission-protected API. Arrival advances the canonical journey through `ARRIVED` to `CHECK_IN_REVIEW` using the Phase B transition service.

## Checklist

The default checklist covers identity/contact/payer/consent, referral and required documents, anesthesia questionnaire and informed consent, fasting, bowel preparation, escort, anticoagulants, antiplatelet therapy, diabetes therapy, allergies, pregnancy where relevant, and pacemaker/implants.

Each item uses exactly one of `confirmed`, `not_confirmed`, `not_applicable`, `requires_clinician_review` or `blocked`. Items are categorized and explicitly marked when clinician authority is required.

## Ownership and blockers

Reception and nursing staff may record administrative states, mark a problem blocked or request clinician review. They cannot confirm or dismiss a clinician-owned item. Recording `blocked` or `requires_clinician_review` creates an explicit journey blocker. Later changing the checklist answer does not silently resolve that blocker; an authorized human must use the audited blocker-resolution action.

To reduce repetitive clicking, `POST /api/patient-journeys/{id}/check-in/confirm-administrative` confirms all unresolved non-clinical items in one transaction and writes both item-level and batch audit evidence. Clinician-owned items are deliberately excluded and remain human-reviewed one by one.

Check-in becomes `ready` and advances to `READY_FOR_CLINICIAN` only when every item is confirmed or not applicable and no open blocker remains. The system never performs procedural, fasting, sedation or medication clearance.

## Audit

Arrival/check-in start, each item mutation, grouped administrative confirmation, blocker creation and final workflow transition are recorded through the existing audit and journey-event mechanisms.

## Frontend handoff

The API contract is ready for the `CheckInChecklist` inside the unified Phase I journey workspace. Existing reception screens remain functional; no parallel reception workflow was created.
