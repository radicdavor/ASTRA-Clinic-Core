# Program 1 Phase B1 - Clinical Readiness Source Evidence Mapping

Status: documentation-only evidence mapping

## 1. Svrha

Ovaj dokument definira koje dokaze buduci Clinical Readiness Gate smije koristiti, a koje ne smije koristiti kao sluzbene readiness facts.

Ne implementira source badges, API, UI, audit events ili database model.

## 2. Allowed sources

Buduci Clinical Readiness smije koristiti ove izvore, uz odgovarajuca pravila:

- Patient identity
- Appointment
- Service
- Provider
- Room
- reviewed ClinicalDocuments
- Patient Clinical Knowledge
- Open Questions from reviewed sources
- Clinical Evidence Timeline as audit context
- Reception/admin verification
- Nurse checklist declaration
- Inventory/material availability
- Consent record when future model exists

Allowed source ne znaci automatski clinical clearance.

Svaki izvor mora biti interpretiran u kontekstu odgovorne uloge.

## 3. Forbidden sources

Zabranjeno je koristiti kao official readiness facts:

- unreviewed AI extraction
- draft ClinicalDocument
- rejected ClinicalDocument
- superseded ClinicalDocument
- Patient Clinical Summary alone
- free-text note without source
- AI suggestion without physician review
- unverified patient claim where clinical review is required
- Open Question without reviewed source
- audit event that does not contain clinical source context

Ako je izvor zabranjen kao official fact, moze eventualno biti prikazan kao warning ili pending review samo ako je jasno oznacen i ne utjece samostalno na final readiness.

## 4. Evidence levels

| Evidence level | Meaning | Can support readiness item? | Can clear readiness? | Notes |
| --- | --- | --- | --- | --- |
| `system_record` | Podatak iz ASTRA operativnog zapisa: appointment, service, room, inventory. | Da, za operativne i resource iteme | Samo za neklinicke iteme | Ne zamjenjuje klinicku prosudbu |
| `reviewed_clinical_source` | Reviewed ClinicalDocument ili source-linked Patient Clinical Knowledge. | Da | Moze poduprijeti physician confirmation | Najjaci source za klinicki kontekst |
| `human_attestation` | Izjava/potvrda ovlastene osobe u sustavu. | Da | Ovisi o ulozi i itemu | Mora imati ulogu i audit |
| `patient_declaration` | Izjava pacijenta, npr. fasting ili preparation. | Da, kao declaration | Ne za physician-only pitanja | Moze zahtijevati nurse/physician review |
| `ai_suggestion` | AI-generated concern ili extraction. | Samo kao prijedlog | Ne | Mora ostati oznaceno kao suggestion |
| `missing_evidence` | Dokaz da potreban izvor nedostaje. | Da, kao missing item | Ne | Moze voditi u `needs_missing_document` |

## 5. Audit requirements

Buduca Clinical Readiness implementacija mora auditirati:

- item generated
- item confirmed
- item overridden
- item dismissed
- item resolved
- source linked
- override reason
- responsible role
- source evidence reviewed

Audit mora cuvati razliku izmedu:

- system generated item
- AI suggested item
- human confirmed item
- physician override
- nurse/admin check

## 6. Source badges

Buduci UI mora prikazati source badges za readiness items kada evidence dolazi iz dokumenata ili Patient Clinical Knowledgea.

Source badge treba voditi prema izvornom objektu, npr. ClinicalDocument detailu.

Source badge ne smije prikazati AI suggestion kao source truth.

Ovaj dokument ne implementira source badges.

