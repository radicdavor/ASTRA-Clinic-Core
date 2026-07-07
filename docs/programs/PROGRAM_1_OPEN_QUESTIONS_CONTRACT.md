# Program 1 - Open Questions Contract

Status: Phase A5 contract, demo/pilot only

## 1. Svrha

Open Questions i Unresolved Findings su pregledane, source-linked klinicke knowledge stavke koje trebaju paznju, ali nisu odluke i nisu zadaci.

Njihova svrha je da lijecnik pri otvaranju pacijenta odmah vidi sto je jos nerazrijeseno i iz kojeg reviewed izvora to dolazi.

Ovaj dokument nije:

- implementacija Task enginea
- Clinical Readiness Gate
- Episode-Based Care
- Workflow Engine
- real AI/OCR implementacija
- produkcijsko odobrenje
- certified EMR ili medical-device claim
- dozvola za unos stvarnih pacijentovih podataka

ASTRA u ovoj fazi ostaje demo/pilot sustav. Realni pacijentovi podaci nisu dopusteni.

## 2. Canonical Definitions

### Open Question

Open Question je pregledano, source-linked pitanje ili upozorenje koje ostaje klinicki nerazrijeseno.

Primjeri:

- patologija pending
- follow-up interval treba lijecnicki pregled
- vanjski report treba reconciliaciju
- preporuka iz vanjskog dokumenta zahtijeva klinicki pregled
- H. pylori status nije jasan
- terapijska preporuka treba potvrdu
- dokumenti su medjusobno kontradiktorni

### Unresolved Finding

Unresolved Finding je pregledani, source-linked finding koji jos nije razrijesen u potvrdjeni klinicki zakljucak, surveillance plan, referral ili closure.

Primjeri:

- abnormalni laboratorijski nalaz koji treba interpretaciju
- radioloski nalaz koji trazi follow-up
- patologija koja ceka odluku o daljnjem vodjenju
- prethodni polip bez potvrdjenog surveillance intervala
- estetska nuspojava koja zahtijeva follow-up

## 3. What They Are Not

Open Questions nisu:

- taskovi
- dijagnoze
- terapijske odluke
- Clinical Readiness Gate blokatori
- automatske follow-up narudzbe
- razlozi za zatvaranje epizode
- sluzbene odluke
- upute pacijentu

Open Questions kasnije mogu dovesti do zadatka, plana, readiness upozorenja ili epizodnog follow-upa, ali to nije dio Phase A5.

## 4. Source-Linked Requirement

Svaki Open Question i svaki Unresolved Finding mora imati barem jedan pregledani source document.

Samo `ClinicalDocument` koji zadovoljava oba uvjeta smije hraniti official open questions:

- `review_status=reviewed`
- `physician_reviewed=true`

Unreviewed AI extraction ne moze stvoriti official open question.

`draft`, `needs_physician_review`, `rejected` i `superseded` dokumenti ne mogu stvoriti official open question.

`PatientClinicalSummaryRecord.open_items` sam po sebi ne moze stvoriti official open question jer je summary view, a ne source of truth.

## 5. Display Rules

Open Questions treba prikazati:

- vidljivo
- odvojeno od poznatih problema
- odvojeno od Patient Clinical Summaryja
- odvojeno od najnovijih preporuka
- kao pitanje ili upozorenje
- sa source badgeovima
- s jasnim tekstom da zahtijevaju klinicku paznju, a ne automatsku radnju

UI ih ne smije prikazati kao potvrdjene dijagnoze, zadatke, terapijske odluke ili pacijent-facing upute.

## 6. Future Boundaries

Buduce faze mogu pretvoriti open questions u:

- taskove
- readiness upozorenja
- episode follow-up
- outcome evidence
- patient explanation draft

To je izricito izvan opsega Phase A5.

Phase A5 smije samo ucvrstiti contract, API metadata i UI jasnoću prikaza nerazrijesenih source-linked stavki.
