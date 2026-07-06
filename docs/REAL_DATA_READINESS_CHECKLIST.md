# Real Data Readiness Checklist

ASTRA Clinic Core is not ready for real patient data until every item below is reviewed and signed off by the responsible clinic, legal, security, and operations owners.

## Product Scope

- Confirm the system is used for scheduling, patient flow, inventory, procurement, billing demo workflows, and modular expansion only.
- Confirm it is not treated as a full EMR, certified medical device, or clinical decision support system.
- Confirm real Croatian fiscalization is not enabled while the provider is `noop`.

## Security

- Replace default `JWT_SECRET`.
- Set `APP_ENV=production`.
- Restrict `CORS_ORIGINS` to approved domains.
- Use HTTPS through a production gateway or load balancer.
- Create named users for each person; do not share demo accounts.
- Review all API key scopes and deactivate unused keys.
- Confirm audit logging is enabled and retained.

## Data Protection

- Confirm OIB handling is approved before any real-data use.
- Confirm demo users understand that real OIB values must not be entered while `REAL_DATA_ALLOWED=false`.
- Confirm patient identity matching uses a resolved patient record, not ambiguous free text.
- Define patient data retention policy.
- Document who can export or delete data.
- Validate backup encryption and restore procedure.
- Run a restore test before go-live.
- Confirm database access is restricted to authorized operators.

## Operations

- Verify migrations run cleanly on an empty database.
- Verify seed/reset scripts are not used in production.
- Configure monitoring for backend health, database health, and failed jobs.
- Prepare incident contact list and rollback plan.
- Document support process for clinic staff.

## Pilot Exit Criteria

- No critical issues in the pilot feedback template.
- Daily schedule and appointment state changes are accepted by staff.
- Inventory consumption and purchase receiving match expected stock movement.
- Billing workflow clearly labels demo fiscalization.
- Audit log can answer who changed what and when.
