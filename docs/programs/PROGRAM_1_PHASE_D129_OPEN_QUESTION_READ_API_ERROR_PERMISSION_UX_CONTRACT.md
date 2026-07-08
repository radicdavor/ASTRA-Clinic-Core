# Program 1 Phase D129 - Open Question Read API Error Permission UX Contract

Status: documented after prototype

| State | Runtime behavior | Safe wording boundary | Side effects |
| --- | --- | --- | --- |
| Unauthenticated | 401 | Login is required before source-linked open questions can be shown. | none |
| Permission denied | 403 | User lacks `clinical_open_questions.read`. This does not imply a clinical decision. | none |
| API key denied | 403 | API keys cannot read this sensitive surface. | none |
| Patient not found | 404 | Patient scope is not available. | none |
| Question not found | 404 | Open question is not available in this patient scope. | none |
| Out-of-scope question | 404 | Do not reveal whether the question exists elsewhere. | none |
| Invalid finding filter | 404 | Finding is not available for this patient. | none |
| Empty list | 200 empty list | No displayed source-linked questions in this scope; this does not mean there are no clinical concerns. | none |
| Backend unavailable | 5xx/network | Open question read surface is unavailable; original source documents remain authoritative. | none |

## Forbidden Error Semantics

Errors must not say diagnosis failed, treatment blocked, clearance denied, approval denied, patient unsafe or issue resolved.

## Clinical Boundary

Error states do not create clinical decisions, review outcomes, recommendations, Task, Outcome Evidence, patient messages, appointment status changes or workflow enforcement.
