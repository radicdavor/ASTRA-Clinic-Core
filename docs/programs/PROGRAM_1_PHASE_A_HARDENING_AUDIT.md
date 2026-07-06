# Program 1 Phase A - Hardening Audit

Status: kriticki audit prije nastavka hardening implementacije

## 1. Svrha

Ovaj dokument biljezi trenutno stanje Program 1 Phase A prije dodatnih izmjena koda.

Ovo je:

- kriticki hardening audit
- pregled rizika oko Patient Clinical Knowledge Layera
- dogovoreni redoslijed malih commitova

Ovo nije:

- implementacija nove funkcionalnosti
- compliance odobrenje
- produkcijsko odobrenje
- odobrenje za stvarne podatke pacijenata
- tvrdnja da je ASTRA certificirani EMR ili medicinski uredjaj

ASTRA u ovoj fazi ostaje demo/pilot sustav. Realni pacijentovi podaci nisu dopusteni dok poseban real-data readiness postupak nije odobren.

## 2. Current Strengths

Trenutna baza vec ima nekoliko vaznih zastitnih slojeva:

- `ClinicalDocument.review_status` postoji i eksplicitno odvaja draft, pregled i odbijena/superseded stanja.
- `ClinicalDocument.ai_extraction_status` postoji i eksplicitno odvaja AI ekstrakciju od lijecnickog pregleda.
- Sluzbeno Patient Clinical Knowledge zahtijeva oba uvjeta: `review_status=reviewed` i `physician_reviewed=true`.
- Source-linked contract testovi postoje i cuvaju pravilo da sluzbene tvrdnje moraju imati izvor.
- Patient Clinical Summary vec izlozuje freshness polja: stale reviewed summary, stale draft, zadnji reviewed document timestamp i warning.
- Potvrda zastarjelog draft sazetka vec se blokira HTTP 409 odgovorom kada postoje noviji pregledani dokumenti.
- `/readiness` ostaje Operational Readiness cockpit, a ne Clinical Readiness Gate.

## 3. Main Risks

1. `backend/app/api/routes/core.py` je prevelik i mijesa clinical document, readiness, patient, summary i helper logiku.
2. `reject-summary` moze semanticki pomijesati odbijanje AI ekstrakcije s odbijanjem cijelog izvornog dokumenta.
3. Summary freshness logika postoji, ali treba jace regresijske testove i jasnije UI poruke.
4. Audit event naming je djelomicno nekonzistentan izmedju dokumenta, summaryja i AI akcija.
5. Frontend jos moze vizualno zamutiti razliku izmedju summary viewa i sluzbenog source-linked znanja.
6. Readiness semantika i Python helper semantika mogu se razici ako se izravni SQL uvjeti i helper funkcije razvijaju odvojeno.
7. Program 1 dokumentacija moze kasniti za kodom ako se hardening odluke ne zapisu odmah.

## 4. No-Go Areas

U ovom hardening passu ne graditi:

- Episode-Based Care
- Clinical Readiness Gate
- Task engine
- stvarni AI provider
- stvarni OCR provider
- Workflow Engine
- production deployment
- real-data readiness
- certified EMR ili medical-device claim

Episode Engine ostaje deferred. Primarni smjer ostaje Patient Clinical Knowledge Layer.

## 5. Recommended Commit Sequence

### Commit 2 - Extract patient knowledge service helpers

Smanjiti odgovornost `core.py` premjestanjem cistih helpera za Patient Clinical Knowledge i Patient Clinical Summary freshness u servisni sloj, bez promjene API contracta i bez promjene baze.

### Commit 3 - Harden Patient Clinical Summary freshness tests

Dodati ili ojacati testove koji dokazuju da draft summary koristi samo sluzbene reviewed dokumente, da stale state radi deterministicki i da stale draft ne moze biti potvrdjen.

### Commit 4 - Clarify Patient Clinical Summary UI states

U Patient Workspaceu jasnije odvojiti sluzbeno source-linked znanje, pregledani sazetak pacijenta, AI draft sazetka, stale warning i dokumente koji cekaju lijecnicki pregled.

### Commit 5 - Review AI extraction rejection semantics

Kriticki razjasniti znaci li `reject-summary` odbijanje AI prijedloga ili odbijanje cijelog izvornog dokumenta. Preferirani uski smjer je da endpoint odbija AI ekstrakciju, a ne brise ili odbacuje raw source.

### Commit 6 - Align readiness helper semantics

Uskladiti readiness brojanje dokumenata koji cekaju pregled s istom semantikom koju koristi Patient Clinical Summary, kako izravni SQL i helper logika ne bi divergirati.

### Commit 7 - Normalize audit event naming documentation

Dokumentirati kanonske nazive audit dogadjaja za `ClinicalDocument` i `PatientClinicalSummary`, uz kompatibilnost s postojecim nazivima gdje promjena koda nije niskog rizika.

### Commit 8 - Update Program 1 docs and README links

Minimalno uskladiti Program 1 dokumentaciju i README linkove s hardening odlukama: service extraction, summary kao view, rejection semantics i Operational Readiness.

### Commit 9 - Final regression pass

Zapisati regresijske biljeske, tocno navesti pokrenute provjere, poznate rizike i preporuceni sljedeci zadatak: `Program 1 Phase A5 - Open Questions and Unresolved Findings UI/Contract`.
