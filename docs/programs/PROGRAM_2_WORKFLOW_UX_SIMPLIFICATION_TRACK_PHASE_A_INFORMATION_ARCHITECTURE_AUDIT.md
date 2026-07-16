# Program 2 Workflow UX Simplification Track — Phase A

> Historical record. It is not the current product-state source; see the canonical documents in `docs/`.

## Polazište

- Repozitorij: `radicdavor/ASTRA-Clinic-Core`
- Grana i početni commit: `main` na `a6ec2eb`
- Backend tijeka pacijenta, javne rute, audit, RBAC i model stanja ostaju nepromijenjeni.
- Baseline: frontend typecheck, 21 interaktivni test, contract testovi i production build prolaze.

## Inventar ruta i ulaza

Prije zahvata bočna navigacija ima 20 stalnih i 2 demo stavke. Primarni operativni ulazi su `/`, `/patients`, `/appointments`, `/reception` i `/journeys/:id`. Klinički pomoćni alati su `/clinical-documents`, `/laboratory`, `/therapies`, `/knowledge` i `/gastroenterology`. Operativni pomoćni alati su `/workflow`, `/inventory`, `/suppliers`, `/purchase-orders` i `/invoices`. Administrativne rute su `/services`, `/clinics`, `/modules`, `/audit-log`, `/api-keys` i `/readiness`. Program 1 ostaje demo/development skup pod postojećim rutama.

Sve postojeće rute ostaju registrirane. Mijenjaju se samo vidljivost i grupiranje ulaza u navigaciji.

## Uloge i potreban pristup

| Uloga | Primarni zadaci | Sekundarni alati |
| --- | --- | --- |
| Recepcija | Danas, Pacijenti, Naručivanje | dokumenti, računi i zadaci prema dozvolama |
| Liječnik | Danas, Pacijenti, Znanje | dokumenti, laboratorij, terapije, gastroenterologija |
| Medicinska sestra/tehničar | Danas, Pacijenti | dokumenti, zadaci i inventar prema dozvolama |
| Naplata | Danas, Pacijenti | računi |
| Administrator | svi zadaci | grupirani klinički, operativni, financijski, administrativni i demo alati |

Vidljivost nije autorizacija. Backend dozvole ostaju mjerodavne.

## Nalazi

1. Ravnih 20–22 navigacijskih izbora izlaže interne module umjesto korisničkih zadataka.
2. Globalna pretraga izgleda aktivno, ali nema ponašanje.
3. Dnevna ploča je već sažeta na četiri stupca, ali prikazuje sve filtre odjednom.
4. `Započni prijem` na dnevnoj ploči prije navigacije poziva mutaciju prijema.
5. `Naplati` može izraditi račun prije otvaranja radnog prostora.
6. Klik na pacijenta ne fokusira uvijek stvarno aktualnu fazu.
7. Radni prostor istodobno prikazuje timeline, dokumente, AI sažetak, blokade, prijem, pripremu, pregled, materijal, račun i plaćanje.
8. Središnji radni prostor koristi `any` za glavne API ugovore.
9. Terminologija je uglavnom hrvatska, ali ostaju izrazi poput `Audit log`, `check-in` i tehničke oznake.

## Ciljna informacijska arhitektura

- Najviše četiri primarna ulaza: **Danas**, **Pacijenti**, **Naručivanje**, **Znanje** kada je relevantno.
- **Više** s ne-praznim skupinama prema ulozi: Klinički alati, Organizacija rada, Nabava i zalihe, Financije, Administracija i Demo.
- Dnevna ploča: datum, pretraga i problem kao zadane kontrole; ostalo pod **Dodatni filtri**.
- Klik s dnevne ploče samo otvara odgovarajuću fazu; ne mijenja stanje.
- Radni prostor prikazuje trenutno stanje, jednu sljedeću radnju i samo jednu aktivnu fazu.
- Timeline, dokumenti i AI sažetak nalaze se u sekundarnom **Kliničkom kontekstu**.

## Razine prioriteta

- Razina 1: otvorena blokada i najviše četiri ključna statusa za sadašnju fazu.
- Razina 2: sadržaj jedine aktivne faze.
- Razina 3: timeline, povijesni dokumenti, AI metapodaci i dovršene faze iza jednog otvaranja.

## Ne-ciljevi

Ne mijenjaju se backend workflow, modeli, API rute, audit, naplata, klinička automatizacija ni izvorni dokumenti. Ne uvodi se novi UI framework, command palette, dashboard, workspace ili baza podataka.
