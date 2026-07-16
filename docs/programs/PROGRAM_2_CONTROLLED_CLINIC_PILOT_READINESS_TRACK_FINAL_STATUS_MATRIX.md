# Program 2 Controlled Clinic Pilot Readiness Track — final status matrix

The scope qualifier **synthetic** always means synthetic data in a local or controlled test environment. It does not authorize execution with real patients.

| Capability | Final status | Boundary / evidence |
|---|---|---|
| Canonical workflow | COMPLETE FOR SYNTHETIC PILOT | One PatientJourney path from intake to closure. |
| Role-aware navigation | TESTED | Automated permissions plus synthetic browser role review. |
| Daily dashboard | TESTED | Synthetic rows, filters and role presentation reviewed. |
| Patient Journey Workspace | TESTED | Stage-focused synthetic browser and component evidence. |
| Source documents | COMPLETE FOR SYNTHETIC PILOT | Local upload, checksum, authorization and source view only. |
| AI summary | STUBBED | Deterministic local draft; source linked and review marked. |
| AI diagnosis suggestions | IMPLEMENTED BUT DISABLED | Default off and fail closed; separate per-item UI. |
| ICD validation | BLOCKED | No canonical repository ICD catalog exists. |
| PostgreSQL CI | COMPLETE | PostgreSQL service is mandatory; missing test URL fails the gate. |
| Migrations | TESTED | Unique head, empty upgrade, one-revision downgrade and re-upgrade. |
| Backup | TESTED | Synthetic test database only. |
| Restore | TESTED | Separate synthetic target; count and checksum verified. |
| RBAC | TESTED | Route tests and role-specific browser review. |
| Audit | TESTED | Workflow, AI decision, clinical and financial action coverage. |
| Synthetic pilot accounts | COMPLETE FOR SYNTHETIC PILOT | Reception, nurse, physician, billing and administrator. |
| Synthetic pilot scenarios | COMPLETE FOR SYNTHETIC PILOT | Role tasks, limits, timing and pass/fail criteria documented. |
| Usability evaluation pack | COMPLETE | Observation form and decision thresholds exist; no human results claimed. |
| Pilot runbook | COMPLETE | Narrow synthetic path, start/stop, rollback and evidence steps. |
| Incident runbook | COMPLETE | Mandatory stop conditions and defect/incident capture. |
| Web intake | CONTRACT ONLY | No public surface or live activation. |
| AI secretary | CONTRACT ONLY | No live assistant provider. |
| E-mail | STUBBED | Demo sender only; no delivery claim. |
| SMS | STUBBED | Demo sender only; no delivery claim. |
| Mailbox ingestion | CONTRACT ONLY | Manual-review boundary only. |
| OCR | STUBBED | Local text-only demo provider. |
| Scanner | CONTRACT ONLY | Browser upload; no hardware driver. |
| Fiscalization | STUBBED | Production startup rejects stub configuration. |
| Payment integration | NOT AUTHORIZED | Local manual record only; no payment terminal. |
| Production deployment | NOT AUTHORIZED | No production rollout or operating model. |
| Real-data authorization | NOT AUTHORIZED | `REAL_DATA_ALLOWED=false`; synthetic only. |
| Go-live authorization | NOT AUTHORIZED | Requires a separately authorized track and evidence. |

Final decision: **READY FOR HUMAN SYNTHETIC USABILITY EVALUATION**. This is not decision C and is not an execution authorization.
