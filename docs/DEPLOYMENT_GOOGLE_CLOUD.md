# Google Cloud Deployment Notes

ASTRA Clinic Core is local-first today. This document describes the minimum production direction for a later Google Cloud deployment.

## Suggested Services

- Cloud Run for backend and frontend containers
- Cloud SQL for PostgreSQL
- Secret Manager for database URL, JWT secret and integration credentials
- Cloud Run managed HTTPS or an HTTPS load balancer
- Cloud Logging and Monitoring
- Cloud Storage for encrypted backup exports if backups are not managed only by Cloud SQL

## Required Production Environment

Set:

```bash
APP_ENV=production
JWT_SECRET=<strong random secret with at least 32 chars>
ACCESS_TOKEN_MINUTES=60
CORS_ORIGINS=https://your-clinic-domain.example
DATABASE_URL=postgresql+psycopg://...
```

Startup intentionally fails in production when `JWT_SECRET` is weak or CORS points to localhost.

## Deployment Checklist

- Change default admin credentials.
- Restrict IAM access to production secrets and Cloud SQL.
- Enable HTTPS only.
- Configure Cloud SQL automated backups and point-in-time recovery.
- Test restore before using real patient data.
- Review GDPR data-processing obligations, vendor agreements and access-control policy.
- Keep AI/API keys scoped to the smallest required permission set.

ASTRA Clinic Core is not a certified EMR or certified medical device.
