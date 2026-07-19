# Phase G - Interventions and specimens

Status: implemented and additionally protected by shared readiness validation.

`ProcedureIntervention` is the authoritative record for procedure interventions. `PathologySpecimen` is the authoritative record for pathology specimens. Clinical forms may reference the structured facts, but specimens used for pathology closure are not treated as free-text-only form content.

The clinical activity transition service prevents completion when:

- an intervention has no explicit complication resolution;
- a biopsy has no labelled pathology specimen;
- a required clinical form is not completed.

The shared `ClinicalVisitReadinessValidator` now repeats these checks before billing, payment, and direct journey closure. This prevents a compatibility or administrative path from bypassing activity-level clinical integrity gates.

Pathology case creation validates that every specimen references an intervention from the same activity and that the intervention type is specimen-producing. Retrieved polypectomy specimens are included in the shared readiness gate.

Browser-native `window.prompt` is not used in the Program 2 clinical intervention/specimen workflow. Shared confirmation actions now use an application dialog instead of `window.confirm`.
