# Matrica uloga i radnog tijeka

Frontend prikaz pomaže orijentaciji; backend permission i scope ostaju
autoritativni.

| Persona | Početna ruta | Primarna navigacija | Aktivni kontekst | Namjerno izostavljeno |
| --- | --- | --- | --- | --- |
| Administrator | `/` | Danas; Operacije; Nabava i financije; Administracija; Sigurnost | odabrana članica | klinički sadržaj bez medicinske kategorije |
| Tajnica | `/` | Danas; Pacijenti; Naručivanje; Prijem; Dokumenti | Klinika A | encounter editor, AI sažetak, findings/evidence |
| Medicinska sestra | `/` | Danas; Pacijenti; Zadaci; Klinička podrška; Raspored i zalihe | Klinika A / Ustanova A | API ključevi, system audit, puni billing |
| Liječnik 1 | `/` | Danas; Pacijenti; Klinički rad; Zadaci; Naručivanje | Klinika A / Ustanova A / Provider A | operacije Klinike B kao vlastite |
| Liječnik 2 | `/` | Danas; Pacijenti; Klinički rad; Zadaci; Naručivanje | Klinika B / Ustanova A / Provider B | operacije Klinike A i uređivanje tuđe skice |

## Ključna usporedba

- Tajnica bilježi administrativne činjenice i otvara prijem; ne donosi
  medicinsku odluku.
- Sestra je `medical_staff`, vidi dopušteni klinički kontekst za skrb i medical
  handoff, ali nema administratorske alate.
- Oba liječnika mogu prema policyju čitati pregledani institution-wide
  dokument Ustanove A.
- Clinic A termini nisu vlastite operacije Liječnika 2.
- Autorstvo skice ostaje object-level granica: liječnik čita dopušten zapis,
  ali uređuje samo vlastitu skicu.

## Operativne liste

| Lista | Primarni podaci | Detalj na zahtjev |
| --- | --- | --- |
| Dokumenti | pacijent, dokument, datum, tip, jedan status, radnja | provenance, AI metadata, izvor, audit |
| Računi | pacijent, datum, ukupno, otvoreno, status, radnja | stavke, uplate, dostava, audit |
| Evidencija | vrijeme, korisnik, radnja, objekt, scope, rezultat | event/request/object identifikatori i PHI-safe metadata |

Payment history, delivery history i audit detalj ne učitavaju se za svaki red.
