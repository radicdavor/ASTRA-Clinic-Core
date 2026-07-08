# Program 1 Phase I10 - Security API Key Governance

## API Key Rules

- API keys must not receive sensitive clinical write permissions.
- API keys must not imply review, approval, clearance, override, diagnosis or treatment authority.
- Sensitive read access must remain denied or tightly scoped unless separately approved.
- AI agents and system jobs are denied by default for clinical write/review workflows.

## Production Hardening Requirements

- strong `JWT_SECRET`
- explicit `CORS_ORIGINS`
- HTTPS
- secret rotation plan
- named users instead of shared demo users
- security logging and monitoring
- incident response and revocation procedure

## Decision

No real patient data until security and API key governance are reviewed and approved.

