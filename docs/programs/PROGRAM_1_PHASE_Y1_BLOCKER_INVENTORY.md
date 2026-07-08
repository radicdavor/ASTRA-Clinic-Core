# Program 1 Phase Y1 - Blocker Inventory

| Blocker name | Blocker status | Why it blocks production-readiness | Explicitly not approved | Future evidence required | Runtime implementation allowed now? | Phase Y decision |
| --- | --- | --- | --- | --- | --- | --- |
| Production approval blocker | unresolved | No authorized production path exists. | production use | formal production approval path | no | blocked |
| Real-data approval blocker | unresolved | Real patient data is not approved. | real patient data | real-data governance approval | no | blocked |
| PHI/PII processing blocker | unresolved | PHI/PII processing is not approved. | PHI/PII processing | privacy/legal/security approval | no | blocked |
| Clinical safety blocker | unresolved | Clinical safety review is incomplete. | autonomous diagnosis/treatment | clinical safety review evidence | no | blocked |
| Clinical accountability blocker | unresolved | Clinical responsibility model is not approved. | clinical deployment | accountability model | no | blocked |
| Runtime authorization blocker | unresolved | Production auth/authz/RBAC is absent. | runtime authorization | security architecture and validation evidence | no | deferred |
| Runtime auditability blocker | unresolved | Production audit logging is absent. | production auditability | audit model and validation evidence | no | deferred |
| Patient communication blocker | active no-go | Patient communication safety is unresolved. | patient messaging | separate governance and safety approval | no | prohibited |
| Appointment mutation blocker | active no-go | Appointment mutation workflow safety is unresolved. | appointment status mutation | separate governance and safety approval | no | prohibited |
| Workflow enforcement blocker | active no-go | Workflow enforcement could imply clinical control. | workflow enforcement | separate governance, design, and validation | no | prohibited |
| Clinical write-path blocker | active no-go | Clinical writes are not governed or validated. | clinical write workflows | clinical governance and validation evidence | no | prohibited |
| Validation evidence blocker | unresolved | Production validation package does not exist. | production-readiness claim | validation evidence model and results | no | blocked |
| Deployment governance blocker | unresolved | Deployment control model is incomplete. | live clinical deployment | deployment governance model | no | blocked |
| Rollback/incident response blocker | unresolved | Incident and rollback controls are not validated. | go-live | incident/rollback/restore evidence | no | blocked |
| Documentation consistency blocker | partially documented | Docs must remain aligned before any review. | implementation escalation | consistency review evidence | no | documentation-only clarification |
