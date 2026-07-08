# Program 1 Phase D108 - Open Question Persistence Migration Go/No-Go Matrix

Status: active governance decision

| Area | Status | Allowed for demo/pilot DB foundation | Allowed for runtime workflow | Allowed for production | Blockers | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| Migration draft design | documented | yes | no | no | none | preserve |
| ORM model | implemented passive | yes | no | no | no endpoint/service | keep passive |
| Alembic migration | implemented | yes | no | no | production review missing | test upgrade |
| DB shape tests | implemented | yes | no | no | none | keep in suite |
| Source-linking tests | implemented | yes | no | no | none | keep in suite |
| Lifecycle status tests | implemented | yes | no | no | none | keep in suite |
| Route/service absence guard | implemented | yes | no | no | none | keep in suite |
| CI gate | documented | yes | no | no | production gate missing | preserve |
| Runtime endpoint | not implemented | no | no | no | read/write contracts missing | no-go |
| Read endpoint | not implemented | no | no | no | D110 contract needed | no-go |
| Write service | not implemented | no | no | no | runtime approval missing | no-go |
| Automatic question creation | not implemented | no | no | no | human confirmation missing | no-go |
| Review endpoint | not implemented | no | no | no | review workflow missing | no-go |
| Approve/clear/resolve endpoint | not implemented | no | no | no | forbidden semantics | no-go |
| Task engine | not implemented | no | no | no | out of scope | no-go |
| Outcome Evidence | not implemented | no | no | no | out of scope | no-go |
| Patient messaging | not implemented | no | no | no | out of scope | no-go |
| Automatic diagnosis/treatment | not implemented | no | no | no | unsafe semantics | no-go |
| Production | not approved | no | no | no | governance/legal review missing | no-go |
| Real data | not approved | no | no | no | privacy/legal review missing | no-go |

## Conclusion

DB foundation may be allowed. Runtime endpoints, services, UI, automatic question creation, Task, Outcome Evidence, patient messaging, production and real-data use remain no-go.
