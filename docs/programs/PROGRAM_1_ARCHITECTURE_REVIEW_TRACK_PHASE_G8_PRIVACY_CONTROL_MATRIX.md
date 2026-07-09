# Program 1 Architecture Review Track Phase G8 - Privacy Control Matrix

Status: documentation-only privacy control matrix.

| Privacy concept | Allowed in Phase G | Prohibited in Phase G | Data status | Runtime status | Enforcement status | Future dependency | Current decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Privacy principle | Conceptual discussion | Privacy tooling | Synthetic only | None | None | Privacy/legal review | Allowed as docs only |
| PHI/PII boundary | Prohibition discussion | PHI/PII processing | No PHI/PII | None | None | Privacy/legal review | Prohibited |
| Real-data boundary | Prohibition discussion | Real-data ingestion | Synthetic only | None | None | Data governance review | Prohibited |
| De-identification concept | Conceptual discussion | De-identification tooling | Synthetic only | Not implemented | None | Privacy/legal review | Deferred |
| Anonymization concept | Conceptual discussion | Anonymization pipeline | Synthetic only | Not implemented | None | Privacy/legal review | Deferred |
| Pseudonymization concept | Conceptual discussion | Pseudonymization pipeline | Synthetic only | Not implemented | None | Privacy/legal review | Deferred |
| Consent concept | Conceptual discussion | Consent workflow | Synthetic only | Not implemented | None | Privacy/legal review | Deferred |
| Retention concept | Conceptual discussion | Retention enforcement | Synthetic only | Not implemented | None | Privacy/legal and operations review | Deferred |
| Data-subject rights concept | Conceptual discussion | Rights workflow | Synthetic only | Not implemented | None | Privacy/legal and operations review | Deferred |
| Data minimization concept | Conceptual discussion | Data collection | Synthetic only | Not implemented | None | Privacy/legal review | Deferred |
| Purpose limitation concept | Conceptual discussion | Purpose expansion | Synthetic only | Not implemented | None | Privacy/legal review | Deferred |
| Access governance concept | Conceptual discussion | Runtime access grant | Synthetic only | Not implemented | None | Security/privacy review | Deferred |
| Privacy incident concept | Conceptual discussion | Incident automation | Synthetic only | Not implemented | None | Privacy/legal and operations review | Deferred |
| Deployment concept | Boundary discussion | Production deployment | None | Prohibited | Prohibited | Production governance review | Prohibited |

## Decision

The matrix is conceptual only. It does not authorize privacy tooling, PHI/PII processing, real-data processing, de-identification tooling, anonymization pipeline, pseudonymization pipeline, consent workflow, retention workflow, data-subject rights workflow, production access, clinical deployment, or go-live.
