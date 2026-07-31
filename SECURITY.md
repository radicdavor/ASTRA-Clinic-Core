# Security Policy

ASTRA Clinic Core is a publicly visible, pre-1.0 clinic-operations foundation.
The repository does not currently contain a license, so public visibility must
not be described as a grant of open-source reuse rights. ASTRA is not a
certified EMR or medical device and is not authorized for real patient data.

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
patient, billing, authentication or infrastructure data. GitHub private
vulnerability reporting is not currently enabled and no other verified private
reporting channel is published. Enabling and owning such a channel is an open
repository-owner decision; do not invent or infer a contact address or SLA.

Non-sensitive hardening proposals may use ordinary pull requests without
including exploit details, credentials or real records.

## Secret Handling

- Never commit raw API keys, passwords, private keys or production `.env` files.
- API keys are stored hashed.
- Rotate keys immediately if exposure is suspected.

## Supported Versions

The project is pre-1.0. Security fixes target the current `main` branch.
