# Program 1 Phase C3 - Enforcement Risk Register

Status: risk register before runtime enforcement

| Risk | Description | Severity | Likelihood | Mitigation | Current status | Go/No-Go impact |
|---|---|---|---|---|---|---|
| False reassurance | System wording implies patient is ready when evidence is incomplete. | High | Medium | Safe wording, no approval labels. | Mitigated by docs/smoke, not eliminated. | Runtime enforcement no-go. |
| False blocker | System blocks workflow for incomplete or incorrect reason. | High | Medium | No automatic blocking. | Not implemented. | Runtime enforcement no-go. |
| Alert fatigue | Too many warnings reduce user attention. | Medium | High | Severity/category design and usability review. | Open. | Requires pilot review. |
| Missing document misclassification | External document status is misread. | High | Medium | Source-linked review and physician confirmation. | Open. | Real-data no-go. |
| Medication ambiguity | Anticoagulant or therapy status is unclear. | High | Medium | Human review required. | Open. | Enforcement no-go. |
| Consent ambiguity | Consent state is unclear or stale. | High | Medium | No automatic clearance. | Open. | Enforcement no-go. |
| Sedation escort ambiguity | Escort/readiness data may be outdated. | Medium | Medium | Advisory only. | Open. | Requires workflow design. |
| Template drift | Template rules become stale. | High | Medium | Versioning and governance review. | Partial. | Production no-go. |
| Stale snapshot interpretation | Users interpret old snapshot as current. | High | Medium | Labels and supersession history. | Partial. | Enforcement no-go. |
| Audit overload | Audit volume becomes hard to interpret. | Medium | Medium | Audit runbook. | Partial. | Production no-go. |
| Legal exposure | UI implies certified decision support. | High | Medium | Disclaimer review. | Partial. | Production no-go. |
| Privacy risk | Real patient data used before approval. | High | Medium | Real-data no-go checklist. | Open. | Real-data no-go. |
| Patient harm through automation | Software changes workflow without clinical judgment. | Critical | Low currently | No automation implemented. | Guarded. | Runtime enforcement no-go. |
| Staff overreliance | Staff trust advisory signal too strongly. | High | Medium | Training and wording. | Open. | Requires pilot training. |
| Hidden production claim | Docs/UI imply production readiness. | High | Low | No-go docs. | Partial. | Production no-go. |

## Recommended Next Task

`Program 1 Phase C4 - Enforcement No-Go Matrix`
