# Program 1 Phase N2 - Real Data Governance Control Model

Phase N does not approve use of real patient data.

The Pilot Demo RC1 tag does not approve real patient data.

A future real-data governance approval would be required before any real patient data use.

| Control Name | Purpose | Decision Governed | Owner Type | Required Evidence Before Closure | Required Future Validation | Prohibited Until Closure | Non-Approval Statement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PHI/PII classification | classify sensitive data | what counts as real patient data | Data governance owner | data classification policy | sample review | real-data entry | no real-data approval |
| Synthetic vs real boundary | prevent accidental real data | demo/real separation | Data governance owner | synthetic data rules | demo data audit | mixed demo/real data | no boundary is validated |
| Data minimization | limit collected data | minimum data scope | Legal/privacy owner | minimization policy | data-field review | broad collection | no real-data collection |
| Consent/legal basis | define lawful basis | processing basis | Legal/compliance owner | legal basis documentation | legal review | patient data processing | no lawful basis is granted |
| Role-based data access | restrict access | who may see real data | Security/privacy owner | RBAC matrix | access tests | real-data access | no access approval |
| Environment separation | isolate real/demo data | environment boundary | Engineering/security owners | environment design | separation tests | real-data deployment | no environment approval |
| Audit logging | record access/actions | audit scope | Compliance/security owners | audit policy | audit completeness tests | real-data access | no audit approval |
| Retention/deletion | govern lifecycle | retention and deletion | Legal/data owners | retention policy | deletion/export test | retained real data | no lifecycle approval |
| Export procedure | control export | data export | Data/legal owners | export policy | export test | real-data export | no export approval |
| Backup encryption | protect backups | backup handling | Security/operations owners | encryption policy | restore test | real-data backup | no backup approval |
| Breach response | handle incidents | breach process | Security/legal owners | incident runbook | tabletop drill | live incident claims | no process approval |
| Vendor/DPA review | govern processors | vendor use | Legal/privacy owner | DPA review | vendor assessment | vendor processing | no vendor approval |
| GDPR alignment | align with Croatian/EU rules | privacy compliance | Legal/compliance owner | GDPR/DPIA review | compliance review | real-data processing | no GDPR approval |
| Real-data activation gate | prevent accidental go-live | activation decision | Legal/security/clinical owners | gate checklist | gate rehearsal | real-data use | gate is not closed |
