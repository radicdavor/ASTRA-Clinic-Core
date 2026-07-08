# Program 1 Phase D37 Regression Notes

Status: findings read-only API prototype added

## Implemented

- added `GET /api/patients/{patient_id}/clinical-findings`
- added `GET /api/patients/{patient_id}/clinical-findings/{finding_id}`
- added read-only permission seed `clinical_findings.read`
- denied API key/non-user access by default
- kept responses source-linked and no-decision

## Not Implemented

- findings POST/PATCH/PUT/DELETE endpoint
- findings write service
- frontend UI
- Task engine
- Outcome Evidence
- patient messaging
- automatic diagnosis or treatment
- appointment status mutation
- approval, clearance or override

## Recommended Next Step

`Program 1 Phase D38 - Findings Read API Regression Coverage`

