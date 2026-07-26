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

## Operational projections

Operational appointment, search, workflow and patient-journey responses use
purpose-built schemas. They may expose the minimum identity, time, service,
room and status data needed for clinic operations, but they never embed patient
or appointment free-text notes. Clinical narrative is available only through
separately authorized clinical or patient-detail routes.

Response shapes are stable across roles. Frontend field hiding is never used as
an authorization boundary.

## Clinical document classification

New manually created or directly inserted clinical documents default to
`unclassified`. Standard clinical read paths deny them until an authorized
human reviewer assigns a supported classification. Trusted signed-report and
reviewed ingestion paths must set `clinical` explicitly. Classification
defaults are fail-closed in both the application model and database schema.
