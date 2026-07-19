# Clinical Documentation Reliability — Phase D workflow integrity

## Implemented in this increment

The journey-level consumables compatibility endpoint no longer changes `JourneyActivity.status`. It accepts exactly one already-completed unresolved activity. A multi-activity ambiguity or the absence of a completed activity returns HTTP 409 and directs the caller to the activity-specific endpoint.

`validate_clinical_visit_readiness` is the shared fail-closed clinical gate used before:

- billing preparation;
- recording payment;
- deferring payment;
- direct visit closure;
- the final `PatientJourney` transition to completed.

It verifies:

- every required activity is terminal;
- every report-required completed activity has a completed clinical form;
- consumables for completed activities are resolved when required;
- every non-legacy/non-exempt completed activity has a current signed report;
- every required report passes integrity verification;
- every intervention has an explicit complication resolution;
- every biopsy or retrieved polypectomy has a labelled pathology specimen;
- no journey blocker remains open.

This prevents payment or a direct close call from bypassing the clinical gates. Pending pathology is intentionally outside physical-visit closure and follows the separate pathology lifecycle.

## Regression evidence

- a journey-level consumables call cannot complete a planned activity;
- an incomplete form-required activity blocks billing;
- an unsigned report-required activity blocks billing;
- an unresolved intervention blocks billing;
- existing explicit activity-level material, invoice, payment and closure paths remain covered;
- targeted PostgreSQL-backed tests pass.

## Remaining before Phase D closure

An explicit versioned `ActivityReportPolicy` configuration is still required to replace the current compatibility decision based on `form_resolution_status`. The legacy `JourneyEncounter` write API must also be retired for activity-enabled journeys in Phase J. Therefore this document records implemented hardening, not formal Phase D or track closure.
