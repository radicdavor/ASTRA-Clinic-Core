# Program 1 Phase B0 - Clinical Readiness Roles

Status: documentation-only responsibility model

## Svrha

Ovaj dokument definira tko smije sto uciniti u buducem Clinical Readiness Gate modelu.

Ne uvodi backend kod, frontend kod, API, migracije, task engine ili produkcijsku upotrebu.

## Reception/admin

Reception/admin moze verificirati:

- dolazak pacijenta
- identitet pacijenta
- termin
- kontakt podatke
- jesu li dokumenti zaprimljeni
- payment/admin prerequisites gdje je relevantno
- prisutnost pratnje ako je konfigurirana kao administrativna provjera

Reception/admin ne smije odlucivati:

- postoji li klinicka kontraindikacija
- je li medication risk prihvatljiv
- je li sedation risk prihvatljiv
- je li nerazrijeseno klinicko pitanje prihvatljivo
- moze li se klinicki blok overrideati

## Nurse

Medicinska sestra moze verificirati:

- priprema je zavrsena
- pacijentova izjava o postu/fasting statusu
- vitalni znakovi ako buduci workflow to podrzi
- material readiness
- prisutnost suglasnosti
- osnovne checklist stavke

Medicinska sestra moze flagirati:

- medication issue
- allergy issue
- preparation concern
- missing documentation
- promjenu stanja koja zahtijeva lijecnicki review

Medicinska sestra ne smije samostalno overrideati physician-only blocks.

## Physician

Lijecnik moze:

- potvrditi clinical readiness
- prihvatiti ili overrideati clinical warning
- odluciti moze li se postupak provesti unatoc upozorenju
- odluciti je li nedostajuci dokument prihvatljiv za nastavak
- odluciti blokira li open question postupak
- dokumentirati razlog

Lijecnik ostaje odgovoran za klinicku prosudbu.

## AI assistant

AI assistant moze:

- sazimati pregledane dokaze
- predloziti readiness concerns
- detektirati moguce nedostajuce dokumente
- predloziti checklist items
- objasniti zasto nesto mozda treba review

AI assistant ne smije:

- clearati readiness
- overrideati block
- donijeti autonomnu odluku
- komunicirati final clinical readiness pacijentu bez ljudskog odobrenja
- koristiti unreviewed suggestion kao sluzbeni source

## System

Sustav moze:

- prikazati status
- provesti konfigurirane blockere
- zahtijevati override reason
- pisati audit
- cuvati traceability
- odvojiti operational readiness od clinical readiness

Sustav ne smije:

- izmisljati klinicke cinjenice
- tretirati AI suggestion kao official source
- sakriti uncertainty
- zamijeniti lijecnicku prosudbu

## Responsibility matrix

| Area | Reception/admin | Nurse | Physician | AI assistant | System |
| --- | --- | --- | --- | --- | --- |
| Identity check | Verify | Support | Review if discrepancy | No | Display and audit |
| Appointment/service/resource | Verify | Support | Decide clinical relevance | Suggest concern only | Display status |
| Documents received | Verify presence | Flag missing | Decide clinical adequacy | Suggest missing evidence | Link source |
| Reviewed clinical knowledge | View | View/flag | Interpret and decide | Summarize reviewed evidence | Preserve source links |
| Open Questions | View/route | Flag concern | Decide if blocking | Suggest review need | Display as warning |
| Preparation | Verify admin parts | Verify clinical checklist parts | Decide if inadequate prep blocks | Suggest checklist item | Track configured item |
| Medication risk | No decision | Flag | Decide | Suggest concern | Require review if configured |
| Allergy risk | No decision | Flag | Decide | Suggest concern | Require review if configured |
| Sedation/anesthesia | Verify escort/admin part | Verify checklist part | Decide risk | Suggest concern | Track blocker |
| Consent presence | Verify presence | Verify checklist | Explain/confirm clinical adequacy | No final decision | Require configured evidence |
| Override warning | No, unless admin-only | Only if nurse-allowed | Yes for clinical warnings | No | Require reason and audit |
| Override block | No | No for physician-only | Yes if allowed by governance | No | Enforce role and audit |
| Final clinical readiness | No | No | Yes | No | Display confirmed state |

## Guardrail

Ako nije jasno tko smije rijesiti readiness item, default je:

`needs_physician_review`

Default sigurnost je vaznija od brzine.

