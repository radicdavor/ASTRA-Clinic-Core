# ASTRA Clinical Model

Status: Patient Clinical Summary and Clinical Documents foundation

ASTRA Clinical Model defines how medicine exists inside ASTRA Clinic Core during demo/pilot development. It is not production approval, EMR certification, medical-device certification or permission to use real patient data.

The current primary clinical direction is patient-centered knowledge:

- Patient
- ClinicalDocument
- PatientClinicalSummary

Episode Engine remains experimental/deferred until patient-level knowledge is stable.

## Patient

Patient is the person.

The patient is identified by name, date of birth, OIB when available, phone and e-mail. A patient is not only a number, and no appointment should be created for an unknown patient.

The Patient Workspace should first answer:

- What do we know about this patient?
- What remains unresolved?
- Where did each statement come from?

## ClinicalDocument

ClinicalDocument is the source object for patient knowledge.

It may represent:

- internal note
- internal procedure
- external report
- external laboratory
- external pathology
- external imaging
- referral
- discharge summary
- patient uploaded document
- other source material

ClinicalDocument can contain raw text, AI draft extraction, key findings and recommendations. Unreviewed extraction is not official clinical truth.

## PatientClinicalSummary

PatientClinicalSummary is a concise patient-level summary created from reviewed Clinical Documents.

It may contain:

- summary text
- known conditions
- key findings
- open items
- risks
- last recommendations
- source document IDs
- review status

AI may generate a draft summary. The physician may edit it. Only physician-reviewed summaries are official.

## Internal And External Evidence

ASTRA treats external evidence as first-class clinical input after physician review.

A patient may have a consultation in ASTRA, endoscopy elsewhere, pathology from a hospital and a follow-up note later. ASTRA must preserve those sources instead of pretending all care happened inside one linear episode.

## AI Draft Versus Physician-Reviewed Truth

AI may read and summarize.

AI must not:

- invent diagnoses
- hide uncertainty
- mark knowledge as reviewed
- change official clinical truth without physician confirmation

The physician confirms what becomes official.

## Source Linking

Every official clinical summary must retain source document IDs.

The UI must make it clear which document supports each patient-level statement whenever feasible.

## Why Episode Engine Is Deferred

Clinical Episodes can later organize the patient story, but they should not be the first active clinical workflow.

Patient care is often fragmented across institutions and documents. ASTRA must first know what is known about the patient and where it came from.

## Future Preparation

This model prepares future:

- Episode Engine stabilization
- Workflow Engine
- Knowledge Engine
- Clinical Module SDK
- AI operating layer

Those future systems must use reviewed, source-linked patient knowledge as their evidence base.

## What ASTRA Must Not Do Now

ASTRA must not:

- enable real patient data
- implement real Croatian fiscalization
- present AI drafts as official truth
- implement autonomous medical decisions
- implement Workflow Engine
- implement Knowledge Engine
- add new clinical modules
- make Episode Engine primary
