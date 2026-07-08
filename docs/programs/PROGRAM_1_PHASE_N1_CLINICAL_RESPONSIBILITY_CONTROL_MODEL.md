# Program 1 Phase N1 - Clinical Responsibility Control Model

| Control Name | Purpose | Decision Governed | Owner Type | Required Evidence Before Closure | Required Future Validation | Prohibited Until Closure | Non-Approval Statement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Clinical owner assignment | establish accountability | who owns clinical safety | Clinical owner | owner role definition | governance review | production clinical claims | no owner is assigned by Phase N |
| Clinician final authority | preserve human decision authority | final clinical interpretation | Clinical owner | authority policy | negative wording tests | automated decisions | no clinical sign-off is granted |
| Human-in-the-loop review boundary | define review scope | when human review is required | Clinical owner | review boundary policy | workflow tests | autonomous review completion | no review workflow is implemented |
| Advisory-only behavior | keep system non-decisional | advisory vs decision language | Product/clinical owners | approved language matrix | UI/API wording tests | decision claims | no decision authority is granted |
| Diagnosis/treatment prohibition | prevent clinical automation | diagnosis/treatment boundaries | Clinical owner | prohibition policy | forbidden semantics tests | diagnosis/treatment automation | no automation is authorized |
| Unsafe automation escalation | define response to unsafe behavior | escalation path | Clinical/operations owners | escalation runbook | incident exercise | live automation | no runtime escalation is implemented |
| Clinical incident reporting | define reporting expectations | safety incident handling | Clinical/operations owners | incident report template | incident drill | production incident claims | no incident process is approved |
| Manual review requirement | preserve manual review before decisions | manual review threshold | Clinical owner | manual review policy | review traceability tests | automatic closure | no closure workflow is added |
| Clinical safety review cadence | define recurring review | safety review schedule | Clinical owner | cadence policy | review records | production use | no cadence is active |
| Clinical sign-off prerequisites | define future sign-off evidence | prerequisites for sign-off | Clinical owner | prerequisite checklist | sign-off dry run | production-readiness claim | no sign-off is granted |

Phase N does not create a real approval process, production clinical sign-off, or clinical override workflow.
