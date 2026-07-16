# Program 2 Multi-Service Visit Track — Phase F

## Dashboard and activity workspace

Status: implemented and frontend-tested; extended role-based browser evaluation remains pending.

## One row per arrival

The daily board still returns one row per `PatientJourney`. Filters for clinician, clinic, room and service now match any activity within the arrival instead of only the anchor appointment. A physician therefore sees a patient when assigned to any activity in that arrival, while administrators retain the all-clinician view.

Each row includes a compact activity rail with:

- planned time;
- service;
- clinician;
- room;
- explicit status and semaphore;
- current and next activity identity.

The rail is the deliberate visual signature of the multi-service workflow: it exposes order without multiplying dashboard rows. Hovering or focusing a semaphore gives a textual explanation, so color is never the only status carrier.

## Workspace

The patient workspace adds an activity selector above the existing journey stages. Selecting an activity opens only its versioned clinical form. The renderer uses the controlled field registry and never renders arbitrary HTML.

The clinician can:

- explicitly resolve/open the bound form;
- edit and save structured fields;
- complete the form after required-field validation;
- start the selected activity after reception prerequisites;
- complete the physical activity;
- sign the report separately.

Navigation does not silently mutate workflow state. A button that starts, completes or signs names that mutation explicitly and uses confirmation for irreversible actions.

## Compatibility

Legacy journeys without activity data retain the previous encounter panel. Current API journeys always contain a primary activity. Existing fixed encounter data remains preserved during the transition to the activity-scoped form engine.

## Validation

- Backend dashboard/activity/form tests passed.
- Frontend TypeScript check passed.
- Dashboard and workspace interactive tests passed.
- Production frontend build passed.

