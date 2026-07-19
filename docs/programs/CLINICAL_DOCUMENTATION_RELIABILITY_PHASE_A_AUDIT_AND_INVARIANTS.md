# Clinical Documentation Reliability — Phase A audit and invariants

## Scope and starting point

The reliability track hardens the existing Program 2 aggregate. It does not introduce a second visit workflow. The canonical operational spine is:

`Patient → PatientJourney → JourneyActivity → ClinicalFormInstance → SignedClinicalReport`

`Appointment` is the scheduling record associated with a journey activity. One `PatientJourney` remains one physical arrival and owns one check-in, coordinated billing and payment.

The inspected baseline was `main` at `2c21663`, aligned with `origin/main`. Alembic had one head (`0052_gastro_hardening`) and the working tree was clean before Phase A–C implementation.

## Persistence and mutation audit

| Concern | Canonical path | Finding |
|---|---|---|
| Resolve/open form | `clinical_forms.resolve_instance` | Reuses the active instance or resolves a published binding. |
| Load form | `GET .../activities/{activity_id}/form` | Returns the active non-amended/non-void instance. |
| Save draft | `PATCH .../form` → `update_instance` | Now requires instance and revision tokens; creates one ordered revision and one audit event. |
| Complete form | `POST .../form/complete` → `save_and_complete_instance` | Now persists and validates the submitted visible data atomically. |
| Sign form | `POST .../form/sign` → `sign_instance` | Signs only the exact completed instance and creates the signed report. |
| Amend form | `POST .../form/amend` → `amend_instance` | Creates a new instance and preserves the signed predecessor. |
| Activity transition | `journey_activities.transition_activity` | Canonical audited transition service. |
| Legacy completion | journey-level consumables compatibility | Still requires Phase D retirement because a hidden direct completion branch exists in the inspected baseline. |
| Billing/closure | `journey_closure` and billing services | Phase D must consolidate readiness checks; no Phase A–C closure claim is made. |
| Package materialization | catalog governance service/routes | Existing Phase E foundation; full reliability revalidation remains later in this track. |
| Report delivery | report routes/services | Existing hashed stub-delivery foundation; Phase H revalidation remains later in this track. |
| Pathology closure | pathology service/routes | Existing disposition foundation; Phase I revalidation remains later in this track. |
| Legacy encounter | `journey_encounter` routes | Still writable in the inspected baseline and remains a Phase J item. |

## Non-negotiable invariants

1. A consequential form action receives the exact values visible to the clinician.
2. Completion never validates older persisted data while newer local data is displayed.
3. Changing activity, stage or route never silently discards a dirty clinical form.
4. A stale client never overwrites a newer server revision.
5. Every accepted form mutation creates one ordered revision and one audit event.
6. Only the activity transition service may complete a clinical activity.
7. Billing and closure use one shared clinical-visit readiness decision.
8. Activities whose policy requires a report must have a valid signed report before billing.
9. Signed reports remain integrity-verifiable and immutable.
10. Pathology closure requires an explicit structured communication disposition.
11. Activity-enabled journeys use `ClinicalFormInstance` as their clinical write model and do not dual-write a new `JourneyEncounter`.

Phase B enforces invariants 1, 2 and the form portion of 5. Phase C enforces 3 and 4. Invariants 6–11 remain explicit gates for Phases D–J and prevent premature track closure.

## Data ownership

- Browser local state is an editable working copy, never the authoritative committed record.
- `ClinicalFormInstance.data_json` is the current server state.
- `ClinicalFormRevision` is the ordered mutation history.
- A completed instance is read-only; an amendment creates a successor.
- `SignedClinicalReport` snapshots the signed structured data and rendered content.
- Validation is server-authoritative; the frontend maps structured errors to Croatian field labels.

## Safety boundary

All work remains synthetic-only. No real patient data, live delivery, production deployment or autonomous clinical decision is authorized.
