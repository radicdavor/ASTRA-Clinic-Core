# Program 1 Non-Approval Boundary Registry

All statuses are active / not lifted.

| Boundary ID | Boundary Name | Status | Protected Risk | Static Control Artifact | Runtime Enforcement? | Required Future Implementation | Required Future Validation | Can Phase U Close/Lift? | Current Prohibition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAB-001 | production approval boundary | active / not lifted | unsafe deployment | U4 | no | production gates | production evidence review | no | no production approval |
| NAB-002 | real patient data boundary | active / not lifted | PHI/PII misuse | U4 | no | real-data controls | legal/privacy validation | no | no real patient data |
| NAB-003 | PHI/PII processing boundary | active / not lifted | privacy breach | U4 | no | PHI/PII controls | negative tests | no | no PHI/PII processing |
| NAB-004 | clinical automation boundary | active / not lifted | autonomous care decisions | U2/U3 | no | clinical safety controls | no-go validation | no | no clinical automation |
| NAB-005 | patient messaging boundary | active / not lifted | unauthorized contact | U3/U6 | no | messaging governance if approved | no-go validation | no | no patient messaging |
| NAB-006 | appointment mutation boundary | active / not lifted | workflow mutation | U3/U6 | no | workflow controls if approved | no-go validation | no | no appointment mutation |
| NAB-007 | clinical write-workflow boundary | active / not lifted | unsafe clinical writes | U6 | no | write workflow controls if approved | clinical validation | no | no clinical write workflow |
| NAB-008 | Task engine boundary | active / not lifted | task semantics | U4 | no | task governance if approved | no-go validation | no | no Task engine |
| NAB-009 | Outcome Evidence boundary | active / not lifted | false outcome proof | U4 | no | outcome governance if approved | no-go validation | no | no Outcome Evidence |
| NAB-010 | approval/clearance/override boundary | active / not lifted | false signoff | U5 | no | approval governance if approved | clinical/legal validation | no | no approval/clearance/override |
| NAB-011 | workflow enforcement boundary | active / not lifted | runtime enforcement drift | U3 | no | workflow governance if approved | no-go validation | no | no workflow enforcement |
| NAB-012 | validation claim boundary | active / not lifted | false assurance | U4/U7 | no | validation package | validation review | no | no validation claim |
| NAB-013 | go-live authorization boundary | active / not lifted | live use | U4 | no | go-live process | owner review | no | no go-live authorization |
