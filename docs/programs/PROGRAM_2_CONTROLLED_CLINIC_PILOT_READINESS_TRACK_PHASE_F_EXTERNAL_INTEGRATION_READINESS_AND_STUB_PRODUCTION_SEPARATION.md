# Phase F — External integration readiness and stub/production separation

No real provider is connected or authorized. Demo/stub providers are rejected at production startup when they could appear delivered, OCR-processed, AI-reviewed or fiscally issued.

| Integration | Current implementation / provider boundary | Retry/idempotency/failure | Privacy/security/authorization | Disposition |
|---|---|---|---|---|
| Public web booking | Canonical intake contract; no public surface | Scheduling conflicts only | No public threat/privacy review | CONTRACT ONLY / NOT AUTHORIZED |
| AI secretary | Scoped API concepts | No live dialogue/provider | No unrestricted history; no vendor | CONTRACT ONLY / NOT AUTHORIZED |
| E-mail/SMS | `DemoDeliveryProvider`, queued/sent only | Failure state exists; no delivery receipt | No secrets/provider/DPA | DEMO STUB / PRODUCTION BLOCKED |
| Mailbox ingestion | Envelope + mandatory manual review | No mailbox/retry | Sender never auto-linked | CONTRACT ONLY / NOT AUTHORIZED |
| OCR | `LocalDemoOCRProvider`, text only | Job states/explicit failure | Local source; no vendor | IMPLEMENTED FOR TEST / PRODUCTION BLOCKED |
| Classification | Local metadata candidate | Job states; human review | No external data | DEMO STUB |
| Scanner | Browser upload with scan channel | Upload failure visible | No hardware driver | CONTRACT ONLY |
| Fiscalization | `noop` and Croatia stub | No fiscal delivery/receipt | Production startup guard | DEMO STUB / PRODUCTION BLOCKED |
| Payment terminal | Manual payment record only | Transaction/state/audit; no terminal idempotency | No provider | NOT AUTHORIZED |
| EHR/EMR | None | None | No interface/security review | NOT AUTHORIZED |
| OpenAI diagnosis | Backend Responses boundary; flag/key/catalog/production authorization all required | Explicit 503; no automatic retry | Minimal text, `store:false`; no DPA/DPIA | IMPLEMENTED BUT DISABLED / PILOT BLOCKED |
| Local AI summary | Deterministic source index | Explicit generation/review | No network; visibly draft | IMPLEMENTED FOR TEST |
| Document storage | Local filesystem, UUID path, MIME/size/checksum/path checks | Missing/checksum errors explicit | No encrypted/object-store production design | IMPLEMENTED FOR TEST / PRODUCTION BLOCKED |

Configuration values are documented in `.env.example`. Secrets remain backend-only. No provider may be labelled delivered or production-ready because an interface exists. `APP_ENV=production` rejects `noop`, `croatia_stub`, `local_demo` OCR/reminders and `local_deterministic` summary providers. A disabled fiscalization mode blocks issue rather than simulating success.
