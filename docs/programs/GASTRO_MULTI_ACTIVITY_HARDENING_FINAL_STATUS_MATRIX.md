# Gastro multi-activity hardening — final status matrix

| Capability | Status | Evidence / limitation |
|---|---|---|
| Controlled registries | Implemented, tested | Backend validation and frontend controlled constants |
| Package schedule preview | Implemented, tested | Non-mutating API test |
| Transactional package booking | Implemented, tested | Three activities, one journey, retry idempotency |
| Activity preparation | Implemented, tested | Aggregation, provenance, clinical conflict blocker |
| Repeatable structured forms | Implemented, tested | Stable IDs, required items, maximum, unique labels |
| Gastroscopy/colonoscopy schemas | Implemented, synthetic | Published versioned demo schemas |
| Interventions and specimens | Implemented, tested | Controlled APIs; no browser prompts |
| Pathology communication closure | Implemented, tested | Closure blocked before disposition |
| Signed-report hashing | Implemented, tested | Canonical SHA-256 |
| Database report immutability | Implemented, PostgreSQL-tested | Update/delete rejected by trigger |
| Secure report recipient | Implemented, tested | Verified patient or permissioned alternate |
| Delivery | Stubbed | Local `queued_stub`; no live e-mail |
| Legacy encounter boundary | Implemented, tested by existing suite | New coordinated activities use forms |
| Dashboard room view | Implemented, frontend-tested indirectly | Toggle inside daily board |
| Backend suite | Passed | 516 tests |
| Frontend suite | Passed | 31 interaction tests + 4 contracts |
| Migration / downgrade | Passed | Empty PostgreSQL database |
| Backup / restore | Passed | Synthetic checksum gate |
| Docker images | Passed | Backend health/login; frontend HTTP 200 on port 5174 |
| Full role browser walkthrough | Deferred | Browser-control runtime unavailable |
| Human usability evaluation | Not performed | Explicitly outside Codex evidence |
| Real data / production | Not authorized | Remains prohibited |

