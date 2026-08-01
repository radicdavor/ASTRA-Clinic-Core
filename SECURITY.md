# Security Policy

ASTRA Clinic Core is a publicly visible, Apache-2.0-licensed, pre-1.0
clinic-operations foundation. The software license does not authorize
deployment, production use, clinical use or real patient data. ASTRA is not a
certified EMR or medical device.

## Production Baseline

- Change all default development credentials before deployment.
- Set a strong `JWT_SECRET_KEY`.
- Restrict CORS to trusted domains.
- Use HTTPS only.
- Store secrets outside the repository.
- Configure encrypted backups and restore testing.
- Review RBAC roles and API-key scopes before onboarding users or AI agents.
- Do not deploy real patient data unless a separate owner authorization confirms
  the required legal, privacy, access-control, audit-retention and incident-response gates.

## Reporting

Do not open public issues containing vulnerability details that could expose
patient, billing, authentication or infrastructure data. For sensitive reports,
use GitHub's private Security Advisory flow: [Report a vulnerability](https://github.com/radicdavor/ASTRA-Clinic-Core/security/advisories/new).
Private vulnerability reporting is enabled, but no response SLA or dedicated
security-team contact is promised; operational response ownership remains a
production-readiness gate.

Non-sensitive hardening proposals may use ordinary pull requests without
including exploit details, credentials or real records.

## Secret Handling

- Never commit raw API keys, passwords, private keys or production `.env` files.
- API keys are stored hashed.
- Rotate keys immediately if exposure is suspected.

## Supported Versions

The project is pre-1.0. Security fixes target the current `main` branch.
