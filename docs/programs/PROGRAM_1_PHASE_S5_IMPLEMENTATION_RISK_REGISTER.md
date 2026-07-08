# Program 1 Phase S5 - Implementation Risk Register

All risks are planning items only.

| Risk ID | Risk Description | Impact | Likelihood Concept | Mitigation | Required Owner Type | Blocking Gate | Current Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S-R01 | demo readiness misread as production readiness | unsafe use claims | medium | non-approval language and gates | Product/legal owner | production approval gate | planning only |
| S-R02 | implementation before governance owner assignment | unmanaged controls | medium | owner map before tickets | Product owner | governance gate | planning only |
| S-R03 | access control implemented without auditability | missing accountability | medium | pair WP-04 with WP-05 | Security owner | auditability gate | planning only |
| S-R04 | real-data controls implemented without legal/compliance review | legal/privacy risk | medium | WP-12 before real-data consideration | Legal/privacy owner | real patient data gate | planning only |
| S-R05 | audit logs incomplete or non-queryable | weak evidence | medium | audit completeness tests | Security/compliance owner | auditability gate | planning only |
| S-R06 | negative tests omitted | hidden prohibited paths | medium | WP-07 required | QA owner | validation evidence gate | planning only |
| S-R07 | write-path prevention not tested | clinical write drift | medium | no-write negative tests | QA/clinical owner | clinical write-workflow gate | planning only |
| S-R08 | PHI/PII boundary not validated | privacy breach | medium | PHI/PII negative tests | Privacy/security owner | PHI/PII processing gate | planning only |
| S-R09 | monitoring implemented without escalation process | alert noise or missed action | medium | WP-08 depends on WP-09 | Operations owner | incident response gate | planning only |
| S-R10 | incident process documented but not rehearsed | poor response | medium | tabletop drills | Operations/security owner | incident response gate | planning only |
| S-R11 | rollback plan not tested | failed recovery | medium | rollback/restore drills | Operations/engineering owner | rollback/restore gate | planning only |
| S-R12 | operator training assumed but not evidenced | operator error | medium | training records | Operations owner | operator training gate | planning only |
| S-R13 | control implementation outpaces validation | unproven controls | medium | validation gates before claims | QA owner | validation evidence gate | planning only |
| S-R14 | scope creep into patient messaging or clinical write workflows | prohibited features | medium | gate review and no-go checks | Product/clinical owner | patient messaging and clinical write gates | planning only |
| S-R15 | approval/override logic introduced prematurely | false clinical authority | medium | explicit gate and clinical/legal review | Clinical/legal owner | approval/clearance/override gate | planning only |
