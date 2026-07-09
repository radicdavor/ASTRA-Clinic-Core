# Program 1 Architecture Review Track Phase G7 - Privacy and Real-Data Dependency Map

Status: documentation-only dependency map.

| Area | Current Phase G status | Unresolved dependency | Prohibited current action | Required future review | Current decision |
| --- | --- | --- | --- | --- | --- |
| Privacy/legal review | Not performed | Privacy/legal governance | Claim privacy clearance | Privacy/legal review | Deferred |
| PHI/PII governance | Conceptual only | PHI/PII approval path | Process PHI/PII | Privacy/legal review | Prohibited |
| Real-data governance | Conceptual only | Real-data approval path | Ingest or process real data | Data governance review | Prohibited |
| De-identification review | Conceptual only | De-identification methodology review | Implement de-identification tooling | Privacy/legal review | Deferred |
| Anonymization review | Conceptual only | Anonymization methodology review | Implement anonymization pipeline | Privacy/legal review | Deferred |
| Pseudonymization review | Conceptual only | Pseudonymization methodology review | Implement pseudonymization pipeline | Privacy/legal review | Deferred |
| Consent model | Conceptual only | Consent/legal basis model | Implement consent tooling | Privacy/legal review | Deferred |
| Retention model | Conceptual only | Retention schedule and policy | Implement retention enforcement | Privacy/legal and operations review | Deferred |
| Data-subject rights model | Conceptual only | Rights workflow model | Implement rights workflow | Privacy/legal and operations review | Deferred |
| Data minimization | Conceptual only | Minimization policy | Collect real data | Privacy/legal review | Deferred |
| Purpose limitation | Conceptual only | Purpose limitation policy | Reuse data for undefined purpose | Privacy/legal review | Deferred |
| Access governance | Conceptual only | Access governance model | Grant data access | Security/privacy review | Deferred |
| Audit dependency | Conceptual only | Audit model | Capture real audit/access logs | Audit/security/privacy review | Deferred |
| Incident response dependency | Conceptual only | Privacy incident model | Trigger incident workflow | Privacy/legal and operations review | Deferred |
| Deployment governance | Not performed | Deployment governance model | Authorize deployment | Production governance review | Deferred |

## Decision

No privacy or real-data dependency is closed by Phase G. All privacy/legal, PHI/PII, real-data, de-identification, anonymization, pseudonymization, consent, retention, data-subject rights, access governance, audit, incident, and deployment areas remain future review requirements.
