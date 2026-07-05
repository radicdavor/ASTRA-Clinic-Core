# Security Model

ASTRA Clinic Core uses permission-based RBAC and scoped API keys.

## Actors

- `user`: authenticated with JWT
- `api_key`: authenticated with `X-ASTRA-API-Key`

Every actor exposes a permission set. Route dependencies use `require_permission(...)`.

## High-risk permissions

- `inventory.adjust`
- `inventory.write_off`
- `inventory.transfer`
- `procurement.write`
- `billing.write`
- `billing.mark_paid`
- `admin.manage_users`
- `audit.read`

AI/API keys should receive only the smallest required scope. AI keys must not receive stock, billing or audit permissions unless explicitly approved.

## Audit

Structured audit records include:

- actor type
- user id or API key id
- action
- entity type and id
- before/after JSON where relevant
- request id

Security-sensitive workflows must be covered by tests before production use.
