# Evidencija aktivnosti — operativni popis

Status: Faza E

## Prije

- raw tehnički nazivi radnji i entiteta;
- interni ID kao glavni stupac;
- nije bilo korisnika, scopea ni rezultata;
- nije bilo filtera ni detalja;
- nije bilo jasne razlike između clinic audita i globalnog security audita.

## Poslije

- operativni stupci: Vrijeme, Korisnik, Radnja, Objekt, Scope, Rezultat i jedna
  detail radnja;
- tehnički nazivi prevedeni su u razumljive hrvatske oznake;
- aktivni clinic scope jasno je prikazan;
- filtri za razdoblje, korisnika, kategoriju i rezultat stalno su vidljivi;
- objekt i request ID su napredni filtri;
- raw event type, object ID, request ID, reason code, changed field names i
  provenance prikazuju se tek u read-only draweru.

## PHI-safe granica

Backend i dalje vraća `ClinicAuditEventOut` s `extra="forbid"`. DTO ne sadrži
`before_json`, `after_json`, summary, IP, user agent, klinički tekst, token,
cookie ni request/response body. Drawer koristi isključivo tu sigurnu
projekciju. Vrijednosti promijenjenih polja nikada se ne prikazuju.

Dodani su samo sigurni list podaci: ime aktora, naziv aktivnog scopea i
normalizirani rezultat. Imena aktora učitavaju se jednim grupnim upitom, bez
N+1. Clinic scope i permission `audit.read` nisu promijenjeni.

## Vremensko razdoblje

Backend pretvara granice lokalnog datuma kroz timezone aktivne klinike u UTC.
Završni datum je uključiv. Time se izbjegava rezanje događaja oko lokalne
ponoći i promjene ljetnog računanja vremena.

## Detail ponašanje

Audit detalj ne treba dodatni request jer su dopuštena tehnička polja već dio
malog PHI-safe list DTO-a. Drawer osigurava focus trap, Escape i povrat fokusa.
Zatvaranje briše odabrani događaj iz lokalnog stanja.

## Testni dokaz

Backend testovi potvrđuju clinic scope, PHI sentinel redakciju, grupno ime
aktora i lokalne datumske granice. Frontend testovi potvrđuju razumljive
oznake, safe list, tehničke podatke samo u draweru, odsutnost PHI sentinel
vrijednosti, filtere, scope label i focus ponašanje.
