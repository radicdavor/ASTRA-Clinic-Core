# Phase J — Legacy encounter deprecation

Existing `JourneyEncounter` records remain readable. Existing completed legacy records are not rewritten.

When `CLINICAL_ACTIVITY_FORMS_REQUIRED=true`, package activities, non-primary activities, and activities already resolved to a versioned clinical form reject legacy encounter writes with HTTP 409 and an audited `legacy_encounter_write_denied` event.

Single-service compatibility records explicitly marked `not_required` or `legacy` retain the old write path during migration. New coordinated gastroenterology arrivals use `ClinicalFormInstance` as their clinical source of truth. AI diagnosis suggestions are not moved into the structured activity forms by this track.

