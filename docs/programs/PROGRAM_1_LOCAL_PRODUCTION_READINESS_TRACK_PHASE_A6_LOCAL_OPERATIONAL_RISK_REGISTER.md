# Program 1 Local Production Readiness Track Phase A6 - Local Operational Risk Register

Status: documentation-only risk register. Not deployment approval.

| Risk | Why it matters | Current Phase A decision | Mitigation before future approval |
| --- | --- | --- | --- |
| Local machine access risk | Local access could expose demo materials or misuse the tool | Not approved for real data | Define local access controls |
| Accidental real-data entry risk | A user may type real patient data into a synthetic-only tool | Real data remains prohibited | Add explicit input warnings and review policy |
| Screenshot/export leakage risk | Screenshots or copied output can leave the local machine | Export remains prohibited | Define handling rules before any approval |
| Misleading production-readiness perception risk | Local readiness language can be mistaken for go-live | No production approval | Use non-approval labels |
| UI over-trust risk | A UI can imply operational maturity | No-UI Hold remains active | Require UI Review Track |
| Clinician interpretation risk | Demo output could be overread as advice | Not for clinical use | Keep safety labels visible |
| Missing audit trail risk | Local terminal output has no audit trail | No real-data use approved | Define audit model before real-data track |
| No persistence vs evaluation evidence risk | No persistence limits evidence capture | No persistence approved | Define evidence capture model separately |
| Version confusion risk | Local copies may diverge | No deployment action approved | Define version labeling before candidate use |
| Backup/restore risk | Local artifacts may be lost or copied incorrectly | No production use approved | Define backup policy before approval |
| Incident response gap | Local misuse requires response path | No production use approved | Define incident response model |
| Unauthorized copying risk | Local files can be copied outside governance | No real-data use approved | Define local custody rules |

Current decision: these risks remain unresolved blockers before any future approval.
