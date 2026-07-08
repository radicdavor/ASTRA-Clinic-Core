# Program 1 Phase D84 - Open Question Runtime No-Go Matrix

Status: active governance boundary

## Decision

Open questions from findings remain a contract and passive schema surface only. They do not create runtime workflow, persistence, tasks, outcome evidence, patient messages, diagnosis, treatment, approval, clearance or override behavior.

| Surface | Status | Allowed now | Runtime effect allowed | Blockers | Next action |
| --- | --- | --- | --- | --- | --- |
| Contract | documented | yes | none | none | preserve wording |
| Forbidden semantics | documented | yes | none | none | keep regression guard |
| Source-linking | documented | yes | none | no persistence design yet | design persistence later |
| Human review | documented | yes | none | no review workflow | keep human-mediated |
| Lifecycle taxonomy | documented | yes | none | no runtime status engine | review before persistence |
| Passive schema | implemented | yes | none | no DB or endpoint | keep passive |
| Safety regression | implemented | yes | no-go checks only | none | keep in CI |
| Runtime endpoint | no-go | no | no | workflow and safety review missing | defer |
| DB model/migration | no-go | no | no | persistence design missing | defer |
| Write service | no-go | no | no | runtime boundary missing | defer |
| Automatic creation from finding | no-go | no | no | human confirmation missing | forbid |
| Automatic creation from extraction candidate | no-go | no | no | no AI/OCR runtime approval | forbid |
| Task engine | no-go | no | no | out of scope | forbid |
| Outcome Evidence | no-go | no | no | out of scope | forbid |
| Patient messaging | no-go | no | no | out of scope | forbid |
| Automatic diagnosis | no-go | no | no | unsafe semantics | forbid |
| Automatic treatment | no-go | no | no | unsafe semantics | forbid |
| Production | no-go | no | no | governance incomplete | defer |
| Real data | no-go | no | no | privacy/legal review missing | defer |

## Conclusion

Documentation and passive schemas are allowed. Runtime open-question endpoints, persistence, services and automatic creation remain no-go. Task, Outcome Evidence, patient messaging, diagnosis, treatment, production and real-data use remain no-go.
