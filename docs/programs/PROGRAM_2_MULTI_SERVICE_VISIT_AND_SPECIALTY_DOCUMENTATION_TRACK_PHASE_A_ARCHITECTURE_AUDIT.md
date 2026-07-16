# Program 2 Multi-Service Visit and Specialty Documentation Track — Phase A architecture audit

## Repository decision

- Repository: `radicdavor/ASTRA-Clinic-Core`
- Branch: `main`
- Starting commit: `48a1d80` (`Close Program 2 controlled pilot readiness track`)
- Alignment at opening: `main == origin/main`, clean worktree
- Baseline CI: frontend and backend green; PostgreSQL migrations, full tests, integration gate and synthetic restore passed

The prompt's expected `bd0b78f` is an older closed UX baseline. The three intervening commits are the separately authorized, closed readiness track; they do not introduce a competing visit, activity or form model. No hard-stop condition is present.

## Current one-to-one assumptions

| Area | Current source of truth | Limitation for a multi-service arrival |
|---|---|---|
| Scheduling | `Appointment` has one patient, service, provider, room and time range | A combined arrival requires several appointments without several journeys. |
| Visit aggregate | `PatientJourney.appointment_id` is unique and mandatory | It can remain the anchor, but cannot be the only activity link. |
| Encounter | `JourneyEncounter.journey_id` is unique; fixed general text fields | It remains legacy/primary-activity compatibility, not the source for every specialty report. |
| Check-in | one `JourneyCheckIn` per journey | Correct for one physical arrival and should remain visit-level. |
| Patient forms | `PatientFormTemplate` / `JourneyForm` are patient-facing | They must not become the clinician form engine. |
| Documents | `ClinicalDocument` links patient, appointment and journey | It lacks activity, form-version and immutable signed-version provenance. |
| Consumables | `StockMovement.related_journey_id` | It cannot identify which procedure consumed an item. |
| Billing | one draft invoice is found by anchor appointment | It creates only the anchor service line and has no activity-line idempotency. |
| Dashboard | query joins journey to anchor appointment | One row is correct, but current/next activity and activity rail do not exist. |

## Existing validation that can be reused

`validate_appointment_payload` already validates provider activity/availability, weekly hours, room/service rules, provider-room clinic equality, service duration, and provider/room overlap. New activity scheduling will call this validator rather than duplicate it. It must additionally reject overlapping appointments for the same patient. Existing legacy room behavior is permissive when a room has no service rules; new package/activity materialization will require explicit suitability when a service declares allowed rooms.

`Provider` currently belongs to one clinic through `clinic_id`. The first implementation therefore allows activity movement between clinics only when each activity's selected provider and room belong to the same clinic. A connected-clinic or multi-clinic provider policy does not yet exist and will not be silently inferred.

## Required additive architecture

1. Keep `PatientJourney.appointment_id` as the anchor compatibility field.
2. Add `JourneyActivity`, with one backfilled primary activity per existing journey and optional unique appointment link.
3. Add activity participants without introducing a generic equipment-resource model.
4. Add versioned packages and materialize them into appointments plus activities in one transaction.
5. Add a separate controlled clinician form engine: definition, immutable published version, explicit binding, instance and revision.
6. Resolve forms by explicit IDs and binding priority; never from service-name text.
7. Add activity interventions, pathology case/specimen lifecycle and reviewed-result links.
8. Link signed forms to immutable `ClinicalDocument` versions; signing and physical activity completion remain separate actions.
9. Add activity provenance to consumables and invoice lines and one journey-level invoice identity.
10. Keep the dashboard patient-centric; add a compact activity rail and one primary next action.

## Data and migration compatibility

The migration will be additive and linear after `0046_encounter_findings_opinion`. It will preserve every legacy record, create exactly one required primary activity per current journey, link every legacy encounter to that activity while preserving `journey_id`, keep new provenance nullable for legacy rows, and add uniqueness only after deterministic backfill. Downgrade removes only new structures and columns.

No signed-report model exists, so legacy encounter text will not be silently classified as a signed report. Legacy encounters remain visible as legacy clinical records.

## Audit, RBAC and delivery boundaries

Existing backend audit and permission dependencies are suitable. New mutations require granular permissions and minimized audit summaries; form content is not copied wholesale into general audit payloads. Existing demo communication is a stub. Report delivery may record queued/sent/failed state but cannot claim patient delivery or connect a production provider.

## Phase A decision

Safe additive implementation is feasible. `PatientJourney` remains the one-arrival aggregate, `Appointment` remains the scheduling reservation, and `JourneyActivity` becomes the per-clinical-activity source of truth. Phase B may proceed without destructive replacement.
