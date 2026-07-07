# Program 1 Phase A - Go / No-Go Matrix

Status: arhitektonska odluka nakon Phase A closure

## Svrha

Ova matrica sazimlje sto je nakon Phase A spremno za nastavak, sto je spremno samo uz guardrails, a sto ostaje odgodeno ili zabranjeno.

Matrica nije produkcijsko odobrenje, real-data odobrenje, compliance odobrenje ili certified EMR / medical-device claim.

| Area | Status | Evidence | Decision | Notes |
| --- | --- | --- | --- | --- |
| Patient Clinical Knowledge foundation | Go with guardrails | `ClinicalDocument`, source-linked knowledge, Patient Workspace i regression gate postoje | Nastaviti kao primarnu klinicku osnovu | Samo demo/pilot; nije produkcija |
| ClinicalDocument lifecycle | Go with guardrails | `review_status`, `physician_reviewed`, review endpointi i testovi postoje | Cuvati kao source object lifecycle | Review ostaje ljudska potvrda |
| AI extraction lifecycle | Go with guardrails | AI extraction statusi i reject semantics su ucvrsceni | AI smije predlagati, ne odlucivati | Nema real AI providera |
| Source-linked official knowledge | Go with guardrails | Official knowledge zahtijeva reviewed source dokumente | Cuvati kao temeljno pravilo | Unsourced AI output ne smije postati sluzben |
| Patient Clinical Summary view | Go with guardrails | Summary stale logic i UI labeli postoje | Summary ostaje view, ne source of truth | Stale draft review se blokira |
| Open Questions | Go with guardrails | Open Questions contract i UI odvajanje postoje | Koristiti kao warninge | Nisu taskovi i nemaju lifecycle |
| ClinicalDocument Detail UX | Go with guardrails | Detail UX contract i smoke coverage postoje | Nastaviti jasno odvajati source, AI suggestion i review | Bez redizajna u Phase A closure |
| Clinical Evidence Timeline | Go with guardrails | Read-only endpoint i timeline UI postoje | Cuvati kao audit view | Nije Outcome Evidence object |
| Regression Gate | Go with guardrails | Backend invariant tests, smoke i runbook postoje | Obvezno cuvati prije novih Program 1 promjena | Gate se moze mijenjati samo uz obrazlozenje |
| Backend route modularization | Go with guardrails | A16-A18 split, `core.py` retired | Nastaviti modularni route model | Dublji service split ostaje moguc |
| Operational Readiness | Go with guardrails | Readiness ostaje operational model | Cuvati od Clinical Readiness Gate semantike | Ne smije postati compliance gate |
| Episode-Based Care | Deferred | Episode Workspace/ClinicalPlan postoje kao compatibility/deferred surface | No-Go za immediate primary workflow | Reintroduction tek nakon readiness/task/closure semantike |
| Task engine | Deferred | Open Questions jos nisu taskovi | No-Go za immediate implementation | Prvo treba lifecycle i readiness model |
| Clinical Readiness Gate | Deferred | Operativna readiness postoji, clinical readiness jos nije modelirana | No-Go za implementation; Go za Phase B design | Sljedeci preporuceni smjer je operating model |
| Outcome Evidence | Deferred | Timeline je read-only audit view | No-Go za immediate implementation | Ne stvarati novi object bez posebne odluke |
| Medical Note | Deferred | Summary i documents postoje, formal note output ne | No-Go za immediate implementation | Potreban zaseban design |
| Patient Explanation | Deferred | Nema patient-facing formal outputa | No-Go za immediate implementation | Potreban zaseban safety model |
| Consent lifecycle | Deferred | Nije dio Phase A | No-Go za immediate implementation | Potreban zaseban compliance/safety design |
| Procedure/Treatment templates | Deferred | Service catalog postoji, template engine ne | No-Go za immediate implementation | Ne uvoditi prije readiness modela |
| real AI/OCR | No-Go | Placeholder lifecycle postoji | No-Go | Real provider tek nakon data/file/security/readiness odluka |
| real patient data | No-Go | Demo/pilot guardrails ostaju | No-Go | Zabranjeno do posebnog real-data approval procesa |
| production readiness | No-Go | README i docs eksplicitno ogranicavaju demo/pilot | No-Go | Nema produkcijskog odobrenja |
| certified EMR / medical-device status | No-Go | README i Architecture docs zabranjuju claim | No-Go | Ne tvrditi certifikaciju |
| Phase B planning | Go | Phase A closure je spreman | Go | Dokumentacijski prvi korak |

## Zakljucak

Phase A temelji su `Go with guardrails`.

Phase B planning je `Go`.

Production, real patient data, real AI/OCR i certified EMR / medical-device status ostaju `No-Go`.

Clinical Readiness Gate, Task engine, Episode-Based Care, Workflow Engine i Outcome Evidence ostaju odgodeni za posebne odluke.

