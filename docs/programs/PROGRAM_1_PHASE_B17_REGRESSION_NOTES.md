# Program 1 Phase B17 - Regression Notes

Status: frontend read-only history surface

## Implemented

B17 dodaje read-only prikaz Clinical Readiness Snapshot historyja u Appointment Workspace.

Implementirano:

- frontend tipovi `ClinicalReadinessSnapshotHistoryItem` i `ClinicalReadinessSnapshotHistoryResponse`
- API client read metoda `getClinicalReadinessSnapshotHistory`
- Appointment Workspace sekcija `Povijest snapshotova klinicke spremnosti`
- non-blocking error state ako history endpoint nije dostupan
- empty state ako termin nema spremljenih snapshotova
- summary prikaz snapshot metapodataka
- smoke coverage za read-only UI povrsinu i zabranjene write/approval kontrole

## Behavioral changes

Dodana je nova frontend read-only povrsina za prikaz vec spremljenih snapshotova.

Nema nove backend rute.

Nema nove frontend write akcije.

## API compatibility

B17 koristi postojeci B16 endpoint:

`GET /api/appointments/{appointment_id}/clinical-readiness-snapshots`

Nije dodan novi API path.

Nije dodan frontend POST/capture poziv.

## Safety properties

B17 cuva sljedece granice:

- Appointment Workspace samo cita snapshot history
- history UI ne stvara snapshot
- history UI ne mijenja appointment status
- history UI ne stvara Task
- history UI ne stvara Outcome Evidence
- history UI ne stvara override
- history UI ne prikazuje snapshot kao clinical approval
- error history endpointa ne blokira Appointment Workspace
- UI tekst ostaje preview-only i read-only

## Not implemented

B17 nije implementirao:

- capture button
- reason modal
- frontend POST/capture action
- snapshot detail UI
- supersession UI
- edit/delete
- Outcome Evidence
- Task engine
- override
- appointment status change
- clinical approval
- patient messaging
- real AI/OCR
- real patient data

## Remaining risks

- frontend capture workflow jos ne postoji
- user-facing reason modal jos ne postoji
- snapshot detail panel jos ne postoji
- supersession UX jos ne postoji
- history UI ovisi o B16 backend endpointu i korisnickoj read permission konfiguraciji
- produkcijska governance pravila za Clinical Readiness i dalje nisu kompletna

## Go / No-Go

Go za sljedeci ograniceni UI korak:

`Program 1 Phase B18 - Snapshot Capture UI Reason Modal`

B18 smije dodati capture UI samo ako:

- history read surface ostane stabilan
- reason je obavezan
- capture permission se postuje
- UI labeli ostanu preview-only
- nema approval/clearance formulacija
- nema Task, Outcome Evidence, override ili appointment status promjene

No-Go za:

- capture bez razloga
- capture bez permission provjere
- edit/delete snapshot
- supersession workflow
- Task engine
- Outcome Evidence
- appointment status change
- clinical approval

## Recommended next task

`Program 1 Phase B18 - Snapshot Capture UI Reason Modal`
