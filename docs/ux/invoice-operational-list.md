# Računi i plaćanja — operativni popis

Status: Faza D

## Prije

- popis nije prikazivao pacijenta;
- prikazivao je dva raw statusa bez hijerarhije;
- nije prikazivao otvoreni iznos;
- prvi račun automatski je otvarao inline detalj;
- `/api/invoices` je unaprijed vraćao stavke i sve uplate svakog računa;
- payment history je zato bio eager-loaded i za neotvorene račune.

## Poslije

- šest stupaca: Pacijent, Datum, Iznos, Otvoreno, Status, Radnja;
- broj računa je sekundarni red uz pacijenta;
- jedan razumljiv operativni status;
- `0,00` otvorenog iznosa prikazuje se kao `Plaćeno`;
- jedna primarna radnja prema statusu i backend capabilityju;
- dodatne radnje su u meniju;
- stavke i povijest uplata učitavaju se tek otvaranjem dostupnog drawera;
- drawer ima focus trap, Escape, povrat fokusa i vlastiti loading/error state.

## Lagana backend projekcija

Novi kompatibilni endpoint `/api/invoices/operational-list` ne mijenja postojeći
`/api/invoices`. Vraća samo list podatke, izračunati plaćeni i otvoreni iznos,
broj uplata i capability zastavice. Ne vraća `lines` ni `payments`.

Upit zadržava `require_active_clinic("billing.read")` i izričito filtrira
`Invoice.clinic_id` aktivnom klinikom. Capability zastavice ne daju ovlast;
POST endpointi i dalje zasebno provjeravaju `billing.write` i
`billing.mark_paid`.

## Statusni prioritet

Storniran → refundiran → plaćen → djelomično plaćen → odgođeno → nacrt →
spreman za izdavanje → otvoren.

Primarna radnja je `Izdaj račun`, `Evidentiraj uplatu`, `Nastavi naplatu` ili
read-only `Otvori račun`, ovisno o statusu i stvarnoj backend capability
projekciji.

## Request ponašanje

Početno otvaranje šalje jedan lagani list request. Drawer šalje jedan invoice
detail request tek nakon radnje korisnika. Mutacija zatim osvježava samo taj
detail i njegovu list projekciju u memoriji; AppShell i nepovezani moduli ne
učitavaju se ponovno.

## Testni dokaz

Backend testovi provjeravaju izračun otvorenog iznosa, odsutnost stavki/uplata,
aktivni clinic scope i read-only capabilityje. Frontend testovi provjeravaju
stupce, statuse, primarnu radnju, odsutnost eager detail/payment requesta,
otvaranje detalja i skrivanje financijskih mutacija bez capabilityja.
