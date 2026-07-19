# Phase H - Signed-report integrity and secure delivery

Status: implemented for local synthetic evaluation; live delivery remains stubbed.

Every signed clinical report receives a canonical SHA-256 digest over rendered report content and deterministically sorted structured JSON. Report preview, print, delivery, visit-document listing, billing readiness, and closure readiness verify report integrity and fail closed on mismatch.

The database protects signed report content with PostgreSQL immutability triggers introduced by the gastro hardening migration chain. Amendments create a new signed report version and supersede the previous one instead of editing the protected signed content.

Report delivery uses dedicated permissions:

- `reports.read`
- `reports.print`
- `reports.send`
- `reports.send_alternate_recipient`
- `reports.delivery_history`

The default recipient must be the verified patient e-mail. Alternate recipients require the alternate-recipient permission and a reason. Delivery requests are idempotent and record the exact report version.

Delivery remains `queued_stub` in local demo mode. The module does not claim real sent or delivered status and does not authorize live e-mail or SMS.
