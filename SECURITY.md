# Security Policy

ASTRA Clinic Core is an early open-source clinic operations foundation. It is not a certified EMR and not a certified medical device.

## Production warning

- Default credentials are development-only.
- Change `JWT_SECRET` before any non-local deployment.
- Change the default admin password immediately.
- Configure production CORS explicitly.
- Use HTTPS only.
- Back up PostgreSQL and test restore procedures.
- Real patient data requires GDPR-compliant hosting, vendor assessment, access controls, logging and operational policies.

## Vulnerability reporting

Do not publish exploitable security details in public issues. Report vulnerabilities privately to the repository maintainer until a dedicated security advisory process is configured.

## Secret handling

- Never commit raw API keys, passwords, private keys or production `.env` files.
- API keys are stored hashed.
- Rotate keys immediately if exposure is suspected.

## Supported versions

The project is pre-1.0. Security fixes target the current `main` branch.
