# Program 1 Phase D96 - Open Question Persistence No-Go Matrix

Status: active governance boundary

| Area | Status | Allowed now | Runtime behavior allowed | Blockers | Next action |
| --- | --- | --- | --- | --- | --- |
| Persistence design | documented | yes | no | none for docs | preserve |
| Database shape review | documented | yes | no | migration deferred | review later |
| Source-linking rules | documented | yes | no | DB constraints not implemented | review later |
| Lifecycle status persistence | documented | yes | no | no DB status column | review later |
| Review metadata | documented | yes | no | no review workflow | review later |
| ORM deferral | documented | yes | no | intentional | revisit D99 or later |
| Migration review gate | documented | yes | no | migration not approved | use before migration |
| Passive schema | implemented | yes | passive only | none | keep passive |
| Runtime endpoint | not implemented | no | no | safety review missing | no-go |
| DB model/migration | not implemented | no | no | migration gate not passed | no-go |
| Write service | not implemented | no | no | no runtime approval | no-go |
| Automatic question creation | not implemented | no | no | human confirmation missing | no-go |
| Task engine | not implemented | no | no | out of scope | no-go |
| Outcome Evidence | not implemented | no | no | out of scope | no-go |
| Patient messaging | not implemented | no | no | out of scope | no-go |
| Automatic diagnosis/treatment | not implemented | no | no | unsafe semantics | no-go |
| Production | not approved | no | no | governance incomplete | no-go |
| Real data | not approved | no | no | privacy/legal review missing | no-go |

## Conclusion

Open question persistence design is allowed. ORM model and migration remain deferred. Runtime endpoint, automatic creation, Task, Outcome Evidence, patient messaging, production and real-data use remain no-go.
