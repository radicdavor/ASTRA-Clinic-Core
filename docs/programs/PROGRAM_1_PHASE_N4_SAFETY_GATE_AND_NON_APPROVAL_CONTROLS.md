# Program 1 Phase N4 - Safety Gate and Non-Approval Controls

| Gate Name | Protects | Current Status | Required Future Prerequisites | Required Owner Types | Required Evidence | Required Validation | Current Decision | Reason Not Closed | Active Prohibition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Production-use gate | production operation | not implemented | all P0/P1 controls | product, engineering, security, legal, clinical | full release package | production validation | not closed | no approvals | no production use |
| Real-patient-data gate | PHI/PII | not implemented | real-data governance | legal, privacy, security, clinical | GDPR/DPIA and data policy | privacy/security tests | not closed | no legal basis | no real data |
| Clinical-automation gate | diagnosis/treatment safety | not implemented | clinical safety model | clinical/product owners | automation safety design | negative automation tests | not closed | automation no-go | no clinical automation |
| Patient-messaging gate | patient communication | not implemented | messaging safety/legal model | clinical/legal/product owners | messaging design | message safety tests | not closed | messaging no-go | no patient messaging |
| Appointment-mutation gate | workflow state | not implemented | mutation safety design | product/clinical owners | mutation policy | workflow tests | not closed | mutation no-go | no appointment mutation |
| Task-engine gate | task workflow | not implemented | Task engine design | product/clinical owners | task model | task safety tests | not closed | Task engine no-go | no Task engine |
| Outcome-Evidence gate | outcome claims | not implemented | outcome evidence design | clinical/legal owners | evidence policy | evidence tests | not closed | Outcome Evidence no-go | no Outcome Evidence |
| Clinical-write-workflow gate | clinical state changes | not implemented | write workflow design | clinical/product/legal owners | design and audit evidence | write negative tests | not closed | write no-go | no write workflows |
| Approval/clearance/override gate | approval semantics | not implemented | approval/override governance | clinical/legal/product owners | policy and controls | negative wording/workflow tests | not closed | approval no-go | no approval/clearance/override |
| Workflow-enforcement gate | runtime enforcement | not implemented | enforcement design | product/clinical/security owners | enforcement policy | enforcement tests | not closed | enforcement no-go | no workflow enforcement |

No safety gate is closed by Phase N.

No non-approval boundary is lifted by Phase N.

All existing prohibitions remain active.
