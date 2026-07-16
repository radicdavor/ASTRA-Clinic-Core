# Phase D — Role-based synthetic pilot and usability evaluation pack

This pack prepares human evaluation; it does not claim that evaluation occurred. Use only resettable synthetic data and observe without coaching unless safety requires a stop.

## Accounts and permission boundary

All use password `demo123` in local demo only.

| Role | Account | Permitted focus | Prohibited focus |
|---|---|---|---|
| Reception | `demo.reception@astra.local` | patients, appointments, upload, arrival, administrative check-in | clinical review, encounter completion, payment |
| Nurse/technician | `demo.nurse@astra.local` | preparation, upload/source, check-in recording, consumables | diagnosis, encounter completion, invoice/payment |
| Physician | `demo.physician@astra.local` | source review, clinical blocker, encounter, individual AI review if enabled | billing/payment administration |
| Billing | `demo.billing@astra.local` | completed journey, invoice, payment, defer/closure | clinical note and check-in decision |
| Administrator | `demo.admin@astra.local` | configuration, role verification, audit and failed-action inspection | using broad rights as a normal operational shortcut |

## Synthetic scenarios

Each scenario begins after `app.demo.reset` + `app.demo.seed`. Maximum clicks exclude login and text entry.

| ID / role | Starting state and task | Expected path / target | Max clicks / time | Critical notice and pass criteria |
|---|---|---|---|---|
| R1 Reception | Today list contains a journey with a missing document. Find patient and open journey. | Danas → row action → documents | 3 / 45 s | Correct patient and missing document identified; no wrong row. |
| R2 Reception | Patient not arrived. Mark arrival/start administrative check-in. | Journey → Dolazak → Započni prijem → confirm administration | 4 / 60 s | Arrival recorded; clinical-review item remains unresolved. |
| R3 Reception | Check-in includes clinician-review item. | Read checklist only | 2 / 30 s | Participant names clinician handoff and does not make clinical decision. |
| N1 Nurse | Preparation incomplete. Confirm fasting and record escort state. | Journey → Dokumenti i priprema → individual controls | 4 / 60 s | Correct states saved; no blanket clinical clearance. |
| N2 Nurse | Anticoagulant blocker and source document exist. | Blocker → Klinički kontekst → Dokumenti → source | 4 / 60 s | Blocker and source noticed; blocker not cleared without physician. |
| N3 Nurse | Procedure complete and material pending. | Potrošni materijal → select/quantity → confirm | 5 / 75 s | Correct item/quantity; confirmation understood; stock effect explained. |
| P1 Physician | One patient is ready for clinician. | Danas → next action → Pregled | 2 / 30 s | Correct patient; next action found within 5 s. |
| P2 Physician | Summary and source are available. | Klinički kontekst → summary fact → source | 4 / 60 s | AI status and source linkage recognized; no unsupported fact accepted. |
| P3 Physician | Encounter open with unresolved blocker. Enter six-section note and complete. | Pregled → fields → save → complete confirmation | 4 / 4 min | Blocker reviewed; human note saved; completion explicit. |
| P4 Physician | AI diagnosis feature explicitly enabled in an authorized test fixture. | Request → review each → add or reject one | 4 / 90 s | No automatic insertion; no accept-all; model/source status recognized. If feature is disabled, correct result is explaining the disabled notice. |
| B1 Billing | Procedure complete and consumables confirmed. | Danas → billing → issue invoice | 3 / 60 s | Correct journey and amount; one invoice only. |
| B2 Billing | Issued invoice unpaid. Record full payment. | Payment method → confirmation | 2 / 45 s | Correct amount/method; no duplicate payment. |
| B3 Billing | Payment is deferred. | Defer → reason → closure when allowed | 3 / 60 s | Reason recorded; closure only when prerequisites allow. |
| A1 Administrator | Verify role navigation. | Login as each role / inspect primary actions | 8 / 5 min | No prohibited primary action is visible. |
| A2 Administrator | Inspect one success and one failed action. | Evidencija aktivnosti → filters/details | 4 / 90 s | Actor, action, entity, time and request trace explain state. |
| A3 Administrator | Verify demo-only boundary. | Banner → public config/readiness | 3 / 45 s | `REAL_DATA_ALLOWED=false`, no live provider and no production claim. |

Common failures: selecting adjacent patient, treating yellow status as complete, clearing a clinical blocker administratively, assuming AI text is verified, issuing/recording twice, or searching by internal module names. Any consequential wrong-patient action, missed hard blocker or unauthorized clinical decision is an immediate stop.

Use the observation form and thresholds documents for every participant. Results must be signed and supplied separately before any controlled synthetic clinic pilot decision.
