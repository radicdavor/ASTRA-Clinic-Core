# Program 1 Local Production Readiness Track Final Preserved Holds Record

Status: documentation-only preserved holds record. All holds remain `ACTIVE`.

| Hold name | Status | Scope | Prohibited capability | Reason preserved | Evidence level | Condition for reconsideration | Current decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| No-UI Hold | ACTIVE | UI surfaces and controls | UI, browser UI, local web app, server, API, hosted preview | No UI authorization exists | Documentation only | Explicit UI track authorization | Held |
| Synthetic-Only Hold | ACTIVE | Data inputs and scenarios | Real patient-derived content | Synthetic boundary remains required | Documentation only | Explicit real-data governance track | Held |
| No-Network Hold | ACTIVE | Network behavior | Internet, LAN dependency, cloud, API, database, telemetry, analytics | No runtime verification or network authorization exists | Documentation only | Explicit no-network verification or network governance track | Held |
| No-Persistence Hold | ACTIVE | Runtime artifacts | Saved state, local database, durable logs, browser storage, hidden retained state | Persistence is not authorized or verified | Documentation only | Explicit persistence governance track | Held |
| No-Export Hold | ACTIVE | Output movement | File export, report export, PDF, CSV, spreadsheet, print, screenshot workflow, synchronization | Export remains prohibited | Documentation only | Explicit export governance track | Held |
| No-Integration Hold | ACTIVE | External systems | EHR/EMR, appointment systems, messaging systems, databases, external APIs | Integration is prohibited | Documentation only | Explicit integration governance track | Held |
| No-Real-Data Hold | ACTIVE | Data access | Real-data access, inspection, processing, storage, transmission | No legal/privacy review exists | Documentation only | Explicit real-data governance track | Held |
| No-PHI Hold | ACTIVE | Protected health information | PHI handling | PHI governance is not implemented | Documentation only | Explicit PHI governance track | Held |
| No-PII Hold | ACTIVE | Personal identifiers | PII handling | PII governance is not implemented | Documentation only | Explicit PII governance track | Held |
| No-Clinical-Workflow Hold | ACTIVE | Clinical actions | Patient messaging, appointment mutation, writeback, task creation, workflow enforcement | Clinical workflow is not authorized | Documentation only | Explicit clinical workflow track | Held |
| No-Patient-Messaging Hold | ACTIVE | Communication | Patient messages | Messaging is prohibited | Documentation only | Explicit messaging governance track | Held |
| No-Appointment-Mutation Hold | ACTIVE | Scheduling | Appointment mutation | Appointment mutation is prohibited | Documentation only | Explicit appointment governance track | Held |
| No-Clinical-Writeback Hold | ACTIVE | Records | Clinical writeback | Writeback is prohibited | Documentation only | Explicit clinical writeback governance track | Held |
| No-Autonomous-Clinical-Behavior Hold | ACTIVE | Clinical decision behavior | Autonomous diagnosis, treatment recommendation, triage, patient instruction | Clinical automation is not authorized | Documentation only | Explicit clinical safety track | Held |
| No-Deployment Hold | ACTIVE | Release and environment | Packaging, installer, deployment script, deployment automation, production deployment | Deployment is not authorized | Documentation only | Explicit deployment governance track | Held |
| No-Production-Use Hold | ACTIVE | Operational use | Production use, operational use, staff workflow dependence | Production use is not authorized | Documentation only | Explicit production governance track | Held |
| No-Clinical-Use Hold | ACTIVE | Care context | Clinical use | Clinical use is not authorized | Documentation only | Explicit clinical governance track | Held |
| No-Go-Live Hold | ACTIVE | Launch | Go-live authorization and operational activation | Go-live is not authorized | Documentation only | Explicit go-live governance track | Held |
| No-Phase-I Hold | ACTIVE | Track continuation | Phase I, execution-review track, active next track | Final posture is STOP AND HOLD | Documentation only | New explicit narrowly scoped authorization | Held |
