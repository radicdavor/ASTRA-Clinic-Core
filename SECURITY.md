# Security Policy

ASTRA Clinic Core is an early open-source clinic operations foundation. It is not a certified EMR, not a certified medical device and must not be used with real patient data without a production security and compliance review.

## Production Baseline

- Change all default development credentials before deployment.
- Set a strong `JWT_SECRET_KEY`.
- Restrict CORS to trusted domains.
- Use HTTPS only.
- Store secrets outside the repository.
- Configure encrypted backups and restore testing.
- Review RBAC roles and API-key scopes before onboarding users or AI agents.
- Deploy real patient data only in a GDPR-compliant environment with documented access control, audit retention and incident response.

## Reporting

For now, report security issues privately to the repository owner. Do not open public issues for vulnerabilities that expose patient, billing, authentication or infrastructure data.

## Secret Handling

- Never commit raw API keys, passwords, private keys or production `.env` files.
- API keys are stored hashed.
- Rotate keys immediately if exposure is suspected.

## Supported Versions

The project is pre-1.0. Security fixes target the current `main` branch.
