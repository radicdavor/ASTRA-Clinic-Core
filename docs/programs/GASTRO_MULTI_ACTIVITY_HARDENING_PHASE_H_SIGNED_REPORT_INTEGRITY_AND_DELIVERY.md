# Phase H — Signed-report integrity and delivery

Every newly signed report receives a canonical SHA-256 digest over rendered content and sorted structured JSON. Migration 0052 backfills the same digest for existing reports.

A PostgreSQL trigger rejects signed-content update and row deletion. Only supersession metadata may change when an amendment creates a new signed report. Preview, print, delivery, and visit-document listing fail closed when integrity verification fails.

Delivery requires `reports.send`. The default address must exactly match a verified patient e-mail. An alternate recipient additionally requires `reports.send_alternate_recipient` and a reason. Idempotency prevents duplicate queue events. Local demo mode records `queued_stub`; it never claims sent or delivered.

