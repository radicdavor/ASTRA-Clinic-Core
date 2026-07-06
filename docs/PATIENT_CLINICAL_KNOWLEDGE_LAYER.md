# ASTRA Patient Clinical Knowledge Layer MVP

Status: implemented foundation

This document defines the first Patient Clinical Knowledge Layer inside ASTRA Clinic Core.

It replaces the previous assumption that Episode Engine must be the first post-v0.1 clinical center. Episodes remain in the product, but patient knowledge now comes first.

## Purpose

The Patient Workspace must answer immediately:

- What do we know about this patient?
- What remains unresolved?
- Where did each statement come from?

The physician should not need to read twenty reports before understanding the current known state.

## Core Object

`ClinicalDocument` is the foundation.

It belongs to a patient and may optionally link to an appointment.

Supported source types:

- internal
- external
- scanned
- uploaded

Supported document types:

- consultation
- gastroscopy
- colonoscopy
- pathology
- laboratory
- radiology
- discharge
- referral
- other

## AI Rule

AI never creates official patient knowledge.

AI may extract:

- summary
- key findings
- recommendations

The document must be physician reviewed before it contributes to the Patient Clinical Summary.

## Source Rule

Every summary item contains one or more source document references.

The frontend renders those references as source badges that link to the original Clinical Document workspace.

## OCR Scope

This MVP does not implement a real OCR engine.

The upload endpoint stores metadata, an attachment placeholder and optional raw text. OCR is represented only as an interface placeholder for later implementation.

## API Overview

- `GET /api/clinical-documents`
- `POST /api/clinical-documents`
- `POST /api/clinical-documents/upload`
- `GET /api/clinical-documents/search?q=`
- `GET /api/clinical-documents/{id}`
- `PATCH /api/clinical-documents/{id}`
- `POST /api/clinical-documents/{id}/extract`
- `POST /api/clinical-documents/{id}/review`
- `POST /api/clinical-documents/{id}/reject-summary`
- `GET /api/patients/{patient_id}/clinical-documents`
- `GET /api/patients/{patient_id}/clinical-summary`

## UI Overview

- `/clinical-documents`
- `/clinical-documents/:id`
- Patient Workspace Summary tab
- Patient Workspace knowledge sidebar
- internal/external document tabs
- procedure/pathology/laboratory/imaging tabs
- source badges linking summary statements to original documents

## Readiness

Readiness includes `clinical_documents_review`.

Documents awaiting review are warnings only. They do not block the demo or release by themselves.

## Deferred

Not implemented in this sprint:

- real OCR engine
- real AI provider integration
- automatic medical decisions
- automatic diagnosis creation
- Workflow Engine
- Knowledge Engine
- new clinical modules
- real patient data enablement
