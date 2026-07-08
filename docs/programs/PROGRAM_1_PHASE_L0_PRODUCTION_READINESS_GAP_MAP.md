# Program 1 Phase L0 - Production Readiness Gap Map

| Gap Category | Gap Description | Why It Matters | Current Status | Required Evidence Before Closure | Non-Approval Statement |
| --- | --- | --- | --- | --- | --- |
| Clinical safety gaps | clinical interpretation boundaries are not production-approved | prevents unsafe reliance on read-only context | partially documented | clinician-owned safety review and sign-off criteria | not production-approved |
| Real patient data governance gaps | real-data privacy, consent, retention and breach handling are incomplete | protects PHI/PII and legal obligations | not approved | GDPR/DPIA, legal basis, retention and incident process | no real-data approval |
| Human responsibility gaps | final authority and escalation ownership are not production-governed | avoids unclear responsibility | partially documented | named clinical owner model | no clinical automation approval |
| Access control gaps | role and API key policies need production review | prevents overbroad access | demo/pilot scoped | least-privilege access matrix | no production access approval |
| Auditability gaps | audit retention/export and completeness are not production-approved | supports accountability | partially documented | audit coverage and retention evidence | audit is not Outcome Evidence |
| Validation gaps | current checks are demo validation, not production validation | prevents overclaiming test coverage | demo validated | formal validation package | no production validation claim |
| Operational readiness gaps | support, release and change processes are incomplete | prevents fragile operations | not production-ready | operator runbooks and release governance | no deployment approval |
| Monitoring gaps | production alerts and incident visibility are undefined | supports response and reliability | not started | monitoring/SLO evidence | no live operation approval |
| Rollback and DR gaps | restore and rollback drills are not production-proven | protects data and uptime | not production-drilled | backup/restore and rollback drill records | no disaster recovery approval |
| Training gaps | user training and role comprehension are incomplete | prevents misuse | demo-only | training plan and sign-off | no clinical use approval |
| Legal/compliance gaps | compliance review is incomplete | prevents unlawful use | not approved | legal/compliance sign-off | no certification claim |
| Deployment hardening gaps | secrets, CORS, HTTPS and environment separation need review | protects runtime environment | development/demo posture | hardened deployment checklist | no production deployment approval |
| Data lifecycle gaps | retention, deletion and export policies are incomplete | governs data lifecycle | not approved | lifecycle policy and tested procedures | no real-data lifecycle approval |
| Patient communication gaps | patient messaging is not implemented or governed | prevents unsafe communication | no-go | future design/safety review if ever proposed | no patient messaging approval |
| Appointment mutation gaps | clinical workflow must not mutate appointment status automatically | prevents unintended workflow effects | no-go | future safety design if ever proposed | no appointment mutation approval |
| Clinical write-workflow gaps | findings/open questions/review/timeline write workflows are not approved | prevents unsafe clinical state changes | no-go | separate design, tests, legal and clinical approval | no write workflow approval |

Conclusion: the gap map identifies unresolved areas; it does not close them.
