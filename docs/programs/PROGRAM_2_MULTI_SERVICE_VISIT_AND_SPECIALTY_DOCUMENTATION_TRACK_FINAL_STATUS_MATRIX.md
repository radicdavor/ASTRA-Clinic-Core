# Program 2 Multi-Service Visit and Specialty Documentation Track — Final Status Matrix

| Capability | Status | Evidence / limitation |
|---|---|---|
| One arrival, one journey, multiple activities | Implemented and tested | `JourneyActivity`, dashboard regression and synthetic two-activity arrival |
| Activity appointments, rooms and clinicians | Implemented and tested | additive activity scheduling and conflict validation |
| Service packages | Implemented and tested | versioned package API, publish and materialize |
| Single-service backward compatibility | Implemented and tested | primary activity migration and API tests |
| Versioned clinical forms | Implemented and tested | definitions, immutable published versions, bindings, instances and revisions |
| Form administration | Implemented as governed API | create, clone, validate, publish, retire and bind; dedicated visual editor deferred |
| Specialty form catalog | Implemented and tested | specialist, GI, gynecology, aesthetics, gastroscopy, colonoscopy and HarmonyCa |
| Dashboard activity rail | Implemented and tested | one row per arrival, current/next activity and room |
| Activity workspace | Implemented and tested | selected activity opens only its resolved form |
| Interventions and specimens | Implemented and tested | biopsy, polypectomy and labeled specimen rules |
| Pathology lifecycle | Implemented and tested | later result, clinician review and notification gate |
| Signed reports | Implemented and tested | immutable version, source document and amendment |
| Preview and print | Implemented and tested | exact signed report version |
| Report delivery | Stubbed and explicit | `queued_stub` / `local_demo`; no delivery claim |
| Activity consumables | Implemented and tested | lot/serial provenance retained |
| Coordinated invoice | Implemented and tested | one visit invoice, activity-specific idempotent lines |
| Visit closure with pending pathology | Implemented and tested | pathology becomes post-visit follow-up |
| RBAC | Implemented and tested | backend permission checks remain authoritative |
| Audit | Implemented and tested | meaningful activity, form, report, pathology and financial mutations audited |
| Migrations | Passed | empty PostgreSQL upgrade through `0051`, downgrade/re-upgrade and backup/restore |
| Frontend validation | Passed | typecheck, tests, build and smoke |
| Production providers | Not authorized | email, pathology lab, scanner and related external integrations remain inactive |
| Production deployment / real data | Not authorized | local synthetic demo only |

Closure status: **closed within the authorized local synthetic clinic-operations scope**.
