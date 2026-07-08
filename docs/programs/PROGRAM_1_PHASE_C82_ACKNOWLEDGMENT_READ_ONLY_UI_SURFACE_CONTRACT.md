# Program 1 Phase C82 - Acknowledgment Read-Only UI Surface Contract

Status: read-only UI contract

## Svrha

C82 definira read-only UI surface za Human Review Acknowledgment history u Appointment Workspaceu.

UI prikazuje da je covjek pregledao savjetodavni signal ili snapshot context. UI ne smije prikazati acknowledgment kao clinical approval, readiness clearance, override, resolution ili dozvolu za postupak.

## Placement

Panel se prikazuje u Appointment Workspaceu blizu:

- Savjetodavni signali
- Povijest snapshotova klinicke spremnosti

Panel ne smije biti primarna workflow akcija.

## Relationship to Advisory Signals

Acknowledgment referencira `advisory_signal_key`.

Prikaz mora reci da je signal pregledan kao savjetodavni context, ali ne smije reci da je signal rijesen.

## Relationship to Snapshot History

Ako `snapshot_id` postoji, prikaz smije pokazati safe label:

`Povezano sa snapshot zapisom`

Snapshot ostaje immutable. Acknowledgment ne mijenja snapshot payload.

## UI States

Loading:

`Ucitavanje zapisa ljudskog pregleda savjetodavnih signala...`

Empty:

`Nema zapisa ljudskog pregleda za ovaj termin. To ne znaci da nema klinickih rizika.`

Error:

`Zapisi ljudskog pregleda trenutno nisu dostupni. Ostali dijelovi termina ostaju dostupni.`

Permission denied:

`Nemate dozvolu za prikaz zapisa ljudskog pregleda savjetodavnih signala. Ovo ne mijenja status termina.`

## Safe Labels

Allowed:

- Pregledani savjetodavni signali
- Zapis ljudskog pregleda
- Za ljudsku interpretaciju
- Nije klinicko odobrenje
- Ne mijenja status termina
- Povezano sa snapshot zapisom

Forbidden:

- odobreno
- clearance
- cleared
- override
- resolved
- rijeseno
- pacijent spreman
- postupak odobren
- task created
- poslano pacijentu

## No Actions

Panel ne smije imati:

- acknowledgment button
- approve button
- clear button
- override button
- create task button
- send patient message button

## Zakljucak

Read-only UI panel may be implemented if it remains non-blocking, no-action and semantically separate from clinical decision making.

