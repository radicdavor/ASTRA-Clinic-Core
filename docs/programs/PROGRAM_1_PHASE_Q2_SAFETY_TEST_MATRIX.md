# Program 1 Phase Q2 - Safety Test Matrix

No safety area is validated by Phase Q.

Phase Q only defines the future safety test matrix.

| Safety Area | Risk Addressed | Expected Future Test Type | Positive Test Concept | Negative Test Concept | Required Evidence | Owner Type | Current Status | Can Phase Q Close This? | Reason Not Closed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| advisory-only behavior | user misreads advisory as decision | UI/API safety tests | advisory wording visible | decision wording absent | screenshots/API assertions | Product/QA owner | planned only | no | no tests implemented |
| no autonomous diagnosis | unsafe diagnosis automation | no-go regression | diagnosis fields absent | diagnosis attempt unavailable | forbidden field/route checks | Clinical/QA owner | planned only | no | no validation executed |
| no autonomous treatment recommendation | unsafe treatment automation | no-go regression | treatment wording absent | treatment action unavailable | forbidden wording checks | Clinical/QA owner | planned only | no | no validation executed |
| no production approval path | RC1 misread as production | documentation consistency test | no-go wording present | production-ready wording absent | doc review results | Product/legal owner | planned only | no | no evidence review |
| no real patient data approval path | real-data misuse | data-boundary test | demo-only labels visible | PHI/PII entry rejected/absent | data review | Privacy/QA owner | planned only | no | no controls implemented |
| no PHI/PII ingestion path | PHI intake risk | negative input test | synthetic input allowed | PHI/PII input blocked | negative test output | Security/privacy owner | planned only | no | no PHI test implemented |
| no patient messaging | unauthorized contact | route/client/UI no-go test | no messaging controls | messaging attempt absent | no-go test output | Product/legal owner | planned only | no | no test execution |
| no appointment mutation | workflow mutation risk | route/UI no-go test | status read only | mutation route/action absent | no-go test output | Operations/QA owner | planned only | no | no validation approval |
| no Task engine | task semantics risk | route/schema no-go test | no task surface | task create unavailable | no-go evidence | Product/QA owner | planned only | no | no test implementation |
| no Outcome Evidence | false outcome proof | schema/route no-go test | no outcome surface | outcome creation unavailable | no-go evidence | Clinical/legal owner | planned only | no | no validation approval |
| no approval/clearance/override | false clinical signoff | wording/route no-go test | non-approval copy present | approve/clear/override absent | safety assertions | Clinical/legal owner | planned only | no | no evidence review |
| no clinical write workflow | clinical mutation risk | route/client negative tests | read-only flows pass | write routes/actions absent | no-write report | Clinical/QA owner | planned only | no | no tests executed |
| read-only timeline behavior | timeline becomes workflow | API/UI regression | GET/list display works | POST/action absent | timeline tests | Product/QA owner | planned only | no | no new validation |
| read-only workspace behavior | UI action drift | frontend smoke | read-only panel renders | action buttons absent | smoke report | Product/QA owner | planned only | no | no Phase Q execution |
| acknowledgment/advisory boundary | acknowledgment becomes clearance | contract tests | acknowledgment shown as advisory | clearance wording absent | contract evidence | Clinical/QA owner | planned only | no | no validation approval |
| findings/open questions/extraction boundary | source-linked objects become decisions | API/UI tests | source/provenance visible | diagnosis/treatment absent | boundary evidence | Clinical/product owner | planned only | no | no test execution |
| demo synthetic-data boundary | fake data looks real | data review | demo labels present | real identifiers absent | data audit | Data governance owner | planned only | no | no data audit |
| operator-facing disclaimer boundary | demo claims overstate maturity | doc/smoke review | disclaimers present | production claim absent | review checklist | Product/legal owner | planned only | no | no sign-off |
| known limitations visibility | risks hidden | doc/UI review | limitations linked/visible | limitations absent | review evidence | Product owner | planned only | no | no review completed |
| go/no-go safety gates | gates misread as closed | matrix review | gates open | gate marked closed incorrectly | matrix review | Product/legal/clinical owners | planned only | no | no owner approval |
