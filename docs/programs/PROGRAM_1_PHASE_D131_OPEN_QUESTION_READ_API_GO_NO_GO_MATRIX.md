# Program 1 Phase D131 - Open Question Read API Go/No-Go Matrix

Status: documented

| Area | Status | Decision | Notes |
| --- | --- | --- | --- |
| Read API prototype design | documented | Go | GET-only. |
| Response schemas | implemented | Go | Safe list/detail wrappers. |
| Read permission seed | implemented | Go | `clinical_open_questions.read` only. |
| Read helper | implemented | Go | Side-effect-free mapper. |
| GET list endpoint | implemented | Go | Patient scoped. |
| GET detail endpoint | implemented | Go | Patient scoped. |
| Read tests | implemented | Go | Auth, permission, scope, source linking and no side effects. |
| Write/review route absence | tested | Go | Routes remain absent. |
| Source-linking guard | tested | Go | Source fields and limitations preserved. |
| CI gate | documented | Go | Full suite plus targeted tests. |
| POST/PATCH/PUT/DELETE endpoint | absent | No-go | Write remains forbidden. |
| Review endpoint | absent | No-go | No review workflow. |
| Approve/clear/resolve endpoint | absent | No-go | No clinical approval/clearance/resolution. |
| Frontend UI/client | absent | No-go | Deferred to later phase if selected. |
| Task engine | absent | No-go | Open question is not a task. |
| Outcome Evidence | absent | No-go | Open question is not outcome evidence. |
| Patient messaging | absent | No-go | No notification. |
| Automatic diagnosis/treatment | absent | No-go | Human interpretation required. |
| Production | not approved | No-go | Demo/pilot only. |
| Real data | not approved | No-go | No real patient data approval. |

## Conclusion

GET-only read API is allowed. Write/review endpoints, frontend UI/client, Task, Outcome Evidence, patient messaging, automatic diagnosis/treatment, production and real-data use remain no-go.
