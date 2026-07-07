# Program 1 Phase B26 - Snapshot Governance and Safety Label Stabilization

Status: governance and wording contract

## Purpose

Ovaj dokument stabilizira jezik i UI semantiku oko Clinical Readiness Snapshot capturea, historyja, detaila i supersessiona.

Snapshot ostaje spremljeni preview zapis. Snapshot nije klinicka odluka, nije odobrenje postupka, nije klinicka propusnica, nije Outcome Evidence i nije Task.

## Canonical Labels

Preferirani izrazi:

- `preview snapshot`
- `spremljeni preview zapis`
- `nije klinicka odluka`
- `nije odobrenje postupka`
- `nije Outcome Evidence`
- `zamijenjen novijim preview zapisom`
- `nije zamijenjen`
- `razlog zamjene snapshota`

## Forbidden Labels

Ne koristiti:

- `approved`
- `cleared`
- `procedure allowed`
- `ready to proceed`
- `override accepted`
- `task completed`
- `outcome documented`
- `corrected`
- `deleted`
- `invalid`

## Required Disclaimers

UI mora jasno komunicirati:

- capture sprema trenutni server-side preview
- supersession sprema novi preview zapis i oznacava stari kao zamijenjen
- snapshot ne odobrava postupak
- snapshot ne mijenja appointment status
- snapshot ne stvara Task
- snapshot ne stvara Outcome Evidence

## Active And Superseded Snapshots

Snapshot bez supersession metadata prikazuje se kao:

`Nije zamijenjen`

Superseded snapshot prikazuje se kao:

`Zamijenjen novijim preview zapisom`

Superseded ne smije znaciti:

- stari snapshot je pogresan
- stari snapshot je obrisan
- stari snapshot je ispravljen
- pacijent je spreman
- postupak je odobren

## Permission UX

Ako korisnik nema permission, UI smije prikazati:

`Nemate dozvolu za zamjenu snapshotova.`

UI ne smije skrivati history ili detail samo zato sto korisnik nema supersession permission.

## Why Snapshot Is Not Approval

Snapshot je povijesna kopija preview prikaza. On ne zamjenjuje lijecnicku odluku i ne predstavlja formalni readiness clearance.

## Why Supersession Is Not Correction Or Deletion

Supersession je aditivna veza izmedju starog i novog preview zapisa.

Stari snapshot ostaje citljiv, njegov copied payload se ne mijenja i ne brise se.

## Why History Is Not Outcome Evidence

History prikazuje sto je spremljeno i kada. Ne dokazuje da je klinicki ishod postignut, da je task zavrsen ili da je postupak odobren.
