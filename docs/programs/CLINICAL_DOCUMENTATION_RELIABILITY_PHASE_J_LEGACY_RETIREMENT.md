# Phase J - Legacy clinical write-path retirement

Status: implemented for activity-enabled journeys.

Legacy `JourneyEncounter` records remain readable history. For activity-enabled journeys, clinical documentation is written through `ClinicalFormInstance`, `ClinicalFormRevision`, and `SignedClinicalReport`.

When `CLINICAL_ACTIVITY_FORMS_REQUIRED=true`, package activities, non-primary activities, and activities resolved to versioned clinical forms reject legacy encounter writes with a clear compatibility response and an audit event.

The journey-level consumables compatibility endpoint no longer silently marks an activity completed. It only operates when exactly one already-completed activity is clearly eligible; ambiguous or unresolved multi-activity visits return conflict.

New clinical content for coordinated gastro journeys is not dual-written into both legacy encounter notes and versioned activity forms.
