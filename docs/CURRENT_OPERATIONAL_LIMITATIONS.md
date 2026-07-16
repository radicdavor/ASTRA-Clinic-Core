# Current operational limitations

This is the canonical limitation register.

- No real-data pilot, PHI/PII processing, production deployment or go-live is authorized.
- No public web booking, live AI secretary, mailbox, scanner driver, OCR vendor, SMS, e-mail, payment terminal, fiscalization or EHR/EMR integration is active.
- AI diagnosis suggestions are default-disabled and pilot-blocked because there is no canonical WHO ICD-10 catalog, processor governance, privacy approval or human usability evidence.
- OCR supports local plain text only. PDF/image OCR returns an explicit failure.
- AI summaries are deterministic local drafts; they are not clinical conclusions.
- Communication `sent` means the demo sender accepted the action, not delivery.
- Backup/restore validation covers a synthetic local/test PostgreSQL drill only. Encryption, retention, off-site copies, production credentials, RPO/RTO and operator drills are not approved.
- Monitoring is limited to health checks and logs. Alerting, on-call ownership, centralized observability and incident service levels are absent.
- Privacy/governance gaps include DPIA/DPA, processor review, retention/deletion policy, audit retention, data-subject procedures and clinic-owner permission approval.
- Accessibility has automated semantics/interaction checks but no complete WCAG audit or assistive-technology human evaluation.
- Usability evidence is Codex/browser and automated only. No actual clinic participant thresholds have been measured.
- Universal idempotency keys, distributed job queues, high availability and disaster recovery are not implemented.
- The legacy in-place demo reset is not validated as a Program 2 recovery mechanism; the synthetic runbook rebuilds a separately named test database instead.
- The product is not a certified EMR, medical device, clinical decision system or GDPR-certified solution.

Any limitation affecting identity, blocker visibility, source access, authorization, data integrity, financial duplication or recovery is a mandatory synthetic-pilot stop condition.
