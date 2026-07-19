# Clinical documentation reliability - final status matrix

| Capability | Status | Evidence / limitation |
|---|---|---|
| Atomic form completion | Implemented, tested | Complete request carries current data, expected instance, revision, and idempotency key |
| Stale validation defect | Fixed, browser-tested | Current local `Complications` value completes without prior draft save |
| Draft save | Implemented, tested | `Spremi skicu` creates ordered revisions |
| Dirty activity switching | Implemented, tested | Controlled save/discard/stay dialog |
| Optimistic concurrency | Implemented, tested | Stale clients receive HTTP 409 with server metadata |
| Structured validation labels | Implemented, tested | Frontend maps `fields` and focuses invalid field |
| Central readiness validator | Implemented, tested | Used by billing, payment, deferral, and closure |
| Hidden activity completion removal | Implemented, tested | Legacy consumables endpoint cannot complete activity |
| Package booking | Implemented, tested | Existing `/appointments/package` UI and schedule preview |
| Activity preparation | Implemented, tested | Activity requirements aggregate with provenance |
| Repeatable endoscopy fields | Implemented, tested | Stable item IDs and specimen-label validation |
| Intervention/specimen source of truth | Implemented, tested | Domain records drive pathology and readiness gates |
| Signed-report integrity | Implemented, tested | Canonical SHA-256 and immutable signed content |
| Secure report delivery | Implemented, stubbed | Dedicated permissions, verified recipient, `queued_stub` only |
| Pathology communication disposition | Implemented, tested | Closure blocked until structured disposition |
| Legacy clinical writes | Implemented boundary | Activity-enabled journeys use clinical forms |
| Browser-native clinical confirmation | Improved | Shared `ActionButton` now uses application dialog; legacy appointment/service deletes may still use native confirm |
| Full backend suite | Not reconfirmed in this increment | Targeted backend suites passed; previous full run timed out without failure summary |
| Production use | Not authorized | Synthetic-only hold remains active |
