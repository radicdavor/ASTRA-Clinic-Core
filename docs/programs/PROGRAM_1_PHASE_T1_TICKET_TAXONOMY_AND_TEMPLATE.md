# Program 1 Phase T1 - Ticket Taxonomy and Template

Phase T defines future tickets only. No ticket is executed by Phase T.

## Ticket Taxonomy

| Prefix | Meaning |
| --- | --- |
| GOV | governance control tickets |
| DATA | real patient data / privacy governance tickets |
| ACCESS | identity, access-control, RBAC, least-privilege tickets |
| AUDIT | audit logging, traceability, accountability tickets |
| SAFETY | safety boundary and prohibited workflow prevention tickets |
| VALIDATION | validation, negative testing, regression evidence tickets |
| OPS | monitoring, incident response, rollback, support tickets |
| SECURITY | security, secrets, environment, dependency tickets |
| LEGAL | legal/compliance/GDPR/DPA evidence tickets |
| RELEASE | release/change-control/evidence archive tickets |
| TRAINING | operator runbook and training tickets |

## Risk Classes

| Risk Class | Meaning |
| --- | --- |
| R0 | production/real-data blocking control |
| R1 | high-risk governance or safety control |
| R2 | required operational/security control |
| R3 | supporting control |
| R4 | documentation/cleanup/control hygiene |

## Standard Future Ticket Template

- Ticket ID
- Title
- Category
- Purpose
- Source phase(s)
- Scope
- Explicit out-of-scope items
- Risk class
- Blocking status
- Owner type
- Reviewer type(s)
- Prerequisites
- Implementation requirements
- Acceptance criteria
- Required validation evidence
- Required negative tests
- Required documentation updates
- Required audit/logging considerations
- Required rollback/restore considerations
- Required security/privacy considerations
- Required legal/compliance considerations
- Required clinical safety considerations
- Cannot be considered complete until
- Non-approval statement
- Explicit prohibitions still active
