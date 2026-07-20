# Dashboard-native reception and red flags ? Phase A/B audit

Branch: `codex/dashboard-reception-red-flags`  
Starting commit: `719bdcd Open reception directly from daily dashboard`

## Audit findings

- Daily dashboard rows were already simplified to one operational state and one next action.
- `open_check_in` was still implemented as navigation to the full Patient Journey Workspace with `?focus=arrival&reception=1`.
- The Patient Journey Workspace owned the reception modal, so opening a patient from the dashboard exposed unrelated journey panels before or around reception.
- `complete_reception_check_in()` stored every reception item as `confirmed`, including abnormal notes such as fasting not confirmed or pacemaker present.
- Dashboard red warnings were inferred from `confirmed` items with notes. That made an abnormal finding look semantically ?confirmed/clear?.

## Implemented in this increment

- Reception now opens from the daily dashboard in a floating modal without changing route.
- `Otvori prijem` is the explicit reception action; clicking the patient name remains a link to the canonical patient/journey workspace so clinical users do not accidentally enter the reception modal.
- The modal first shows only general patient data, then a short red-flag list.
- Red flags are exception-based: no positive checklist needs to be clicked when everything is ordinary.
- Red-flag items are stored as `requires_clinician_review`, while the patient still moves to `ready_for_clinician`.
- Non-flagged reception safety items are stored as `not_applicable`, not as false clinical confirmations.
- `patient_data_confirmed` remains the only item automatically marked `confirmed` after patient-data confirmation.
- Dashboard red-warning projection now reads `requires_clinician_review` / `blocked` notes rather than `confirmed` notes.
- Reception completion and medical review are separated: reception may complete and route the patient onward while individual red flags remain pending for a physician/nurse decision.
- Red flags may carry structured details, for example fasting timing, intake type, bowel preparation clarity, escort status, device type, and a short note.
- Activity-scoped red flags can be linked to one or more `JourneyActivity` rows; if no activity is selected, the note is treated as shared for the whole visit.
- Closing the modal preserves the dashboard context: date, filters/search, patient/room view, and focus return to the original action.
- Unsaved changes are protected for `X`, Escape, backdrop close, and browser refresh with controlled options: stay, discard, or save and close.
- The clinical workspace now contains a structured "Podaci evidentirani na prijemu" handoff panel.
- Authorized medical roles can record a minimal medical disposition for each red flag without granting reception a clinical decision path.

## Clinical boundary

Reception records facts and red flags. It does not decide whether a procedure may proceed.

If a red flag exists, the patient can still wait for the physician or anesthesiologist. The warning is carried forward as a visible red signal for medical review.

## Deferred

- Tablet-specific patient self-confirmation mode.
- Procedure-specific dynamic red-flag catalogs beyond the current gastro-oriented baseline.
- Migration of older already-started check-ins that do not contain the new `other_medical_review` item.
- Full focus-trap component extraction and a shared application modal primitive for all clinical workflows.
- Full optimistic-concurrency handling for patient-demographic edits during reception.
