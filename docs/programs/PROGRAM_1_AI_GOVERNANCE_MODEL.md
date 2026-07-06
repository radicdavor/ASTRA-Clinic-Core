# Program 1 - AI Governance Model

Status: arhitektonski model upravljanja AI slojem, bez implementacije u ovom zadatku

## 1. Svrha

AI u ASTRA-i nije liječnik, nije administrator i nije izvor službene istine.

AI je pomoćni sloj koji može:

- strukturirati nestrukturirani tekst
- predložiti sažetak
- izdvojiti moguće klinički relevantne nalaze
- upozoriti na nerazriješena pitanja
- pripremiti nacrt objašnjenja pacijentu
- pripremiti nacrt plana ili zadatka

Službeno stanje nastaje tek kada ga potvrdi ovlašteni čovjek.

## 2. Osnovno Pravilo

AI proposes.

Physician confirms.

ASTRA records both.

Sustav mora uvijek razlikovati:

- AI prijedlog
- ljudsku izmjenu
- ljudsku potvrdu
- službenu kliničku činjenicu
- službenu odluku

## 3. Dopuštene AI Radnje

AI smije predložiti:

- sažetak dokumenta
- ključne nalaze
- otvorena pitanja
- preporuke iz dokumenta
- moguće sljedeće korake
- nacrt Medical Note dokumentacije
- nacrt Patient Explanation teksta
- potencijalne nedostajuće izvore
- upozorenje da je ručni pregled potreban

AI smije raditi samo nad izvorima koji postoje u sustavu ili su eksplicitno uneseni u trenutnom toku.

## 4. Zabranjene AI Radnje

AI ne smije:

- izmišljati podatke
- stvarati službenu dijagnozu
- donositi medicinsku odluku
- označiti dokument pregledanim
- automatski zatvoriti nalaz
- automatski zatvoriti epizodu
- automatski poslati medicinsku poruku pacijentu
- automatski propisati terapiju
- automatski zakazati termin bez dozvole
- prikriti nesigurnost
- prikazati prijedlog kao potvrđenu istinu

Ako izvor ne postoji, AI mora reći da izvor nedostaje.

## 5. Source-Linked Requirement

Svaka AI tvrdnja koja se prikazuje korisniku mora imati izvor.

Minimalni izvorni trag uključuje:

- dokument ili zapis
- datum dokumenta ako postoji
- tip dokumenta
- autor ili ustanova ako postoji
- dio sadržaja iz kojeg je tvrdnja izvedena kada je dostupno

Tvrdnja bez izvora smije biti prikazana samo kao upozorenje ili hipoteza za ručni pregled, nikada kao službena činjenica.

## 6. AI Confidence

AI confidence nije medicinska sigurnost.

Confidence označava koliko je model siguran u vlastitu ekstrakciju ili strukturiranje teksta.

Niska confidence vrijednost mora aktivirati poruku:

`Preporučen je ručni pregled.`

Confidence ne smije zamijeniti liječničku prosudbu.

## 7. Human Review States

AI prijedlog može završiti kao:

- pending_review
- accepted
- edited_and_accepted
- rejected
- superseded
- archived

Samo `accepted` i `edited_and_accepted` smiju hraniti službeni patient knowledge sloj.

## 8. Audit

Audit mora zabilježiti:

- kada je AI prijedlog generiran
- nad kojim izvorima je generiran
- koji korisnik ga je pregledao
- što je prihvaćeno
- što je izmijenjeno
- što je odbijeno
- kada je tvrdnja postala službena
- je li pacijentu poslano objašnjenje

Audit mora jasno razlikovati `AI Suggested` od `Human Confirmed`.

## 9. UI Pravila

AI prijedlog mora biti vizualno označen kao prijedlog.

Službena potvrđena informacija mora biti vizualno odvojena od prijedloga.

Korisnik mora moći otvoriti izvor iz svake važne tvrdnje.

Ako AI prijedlog nema dovoljno izvora, UI mora prikazati upozorenje umjesto tihe pretpostavke.

## 10. Medical Note

Medical Note je profesionalna klinička dokumentacija.

AI smije pripremiti nacrt.

Liječnik mora pregledati, urediti i potvrditi prije finalizacije.

Medical Note ne smije biti zaključana u nevidljivom AI formatu. Mora ostati razumljiva i čitljiva liječniku.

## 11. Patient Explanation

Patient Explanation je pacijentu razumljivo objašnjenje.

AI smije pripremiti nacrt koji objašnjava:

- što je učinjeno
- što je nađeno
- što to znači
- što se čeka
- što pacijent treba učiniti
- kada se javiti
- koji su alarmni simptomi

Liječnik ili ovlašteni korisnik potvrđuje prije slanja ili predaje pacijentu.

## 12. Granice Program 1

Program 1 ne uvodi autonomni AI agent.

Program 1 ne uvodi stvarni AI provider.

Program 1 ne uvodi dijagnostički engine.

Program 1 ne uvodi terapijski decision support kao certificiranu medicinsku funkciju.

Program 1 definira governance koji svaka buduća AI implementacija mora poštovati.

## 13. Minimalni Budući Tehnički Zahtjevi

Buduća implementacija AI sloja mora podržati:

- spremanje izvornog prompt/context traga bez stvarnih produkcijskih podataka u demo modu
- spremanje strukturiranog AI outputa
- status pregleda
- ljudsku potvrdu
- vezu prema izvorima
- audit događaje
- mogućnost odbijanja ili zamjene prijedloga

Ovo su zahtjevi za budući razvoj, ne implementacija u ovom dokumentacijskom zadatku.

