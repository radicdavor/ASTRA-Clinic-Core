# Program 1 Phase B18 - Regression Notes

Status: frontend capture UI with required reason

## Implemented

B18 dodaje prvi frontend capture workflow za Clinical Readiness Snapshot.

Implementirano:

- frontend capture request type
- frontend capture response type
- API client metoda `captureClinicalReadinessSnapshot`
- sigurni capture button label `Spremi snapshot previewa`
- reason-required modal
- client-side validacija praznog razloga
- success handling
- 403/permission error handling
- non-blocking generic error handling
- history refresh nakon uspjesnog capturea
- upozorenje ako je snapshot spremljen, ali history refresh nije uspio
- smoke coverage za capture UI i zabranjene approval/clearance/task signale

## Behavioral changes

Appointment Workspace sada moze pozvati postojeci B15 capture endpoint iz UI-ja.

Capture je eksplicitna korisnicka akcija i zahtijeva razlog.

Nakon uspjesnog capturea Appointment Workspace ponovno ucitava snapshot history.

## API compatibility

B18 ne dodaje nove backend pathove.

Koristi postojeci B15 endpoint:

`POST /api/appointments/{appointment_id}/clinical-readiness-snapshots`

Koristi postojeci B16 endpoint za refresh:

`GET /api/appointments/{appointment_id}/clinical-readiness-snapshots`

Frontend ne salje preview payload.

Frontend salje:

- `reason`
- `client_preview_generated_at` ako je live preview vec ucitan

Frontend ne uvodi dodatnu idempotency logiku jer server-side persistence za idempotency ostaje deferred.

## Safety properties

B18 cuva sljedece granice:

- capture button ne koristi approval/clearance wording
- modal zahtijeva typed reason
- prazan reason ne moze submitati formu
- capture ne mijenja appointment status u UI-ju
- capture ne stvara Task
- capture ne stvara Outcome Evidence
- capture ne stvara override
- capture ne salje patient message
- capture ne uklanja live preview
- history section ostaje vidljiv i kod permission errora
- capture UI ostaje preview-only

## Not implemented

B18 nije implementirao:

- clinical approval
- readiness clearance
- override
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- snapshot edit/delete
- supersession UI
- snapshot detail page
- production governance
- real AI/OCR
- real patient data
- server-side idempotency persistence

## Remaining risks

- permission UX je osnovan i ovisi o backend error porukama
- nema snapshot detail pagea
- nema supersession UX-a
- produkcijska governance pravila jos nisu kompletna
- backend pytest nije potreban za ovu frontend-only fazu, ali ostaje vazan za svaku buducu backend izmjenu
- idempotency persistence ostaje deferred

## Go / No-Go

Go za sljedeci read-only korak:

`Program 1 Phase B19 - Snapshot Detail Read-Only View`

Razlog:

Nakon capture UI-ja korisnici trebaju siguran detail view copied snapshot payloada prije bilo kakve rasprave o supersessionu, edit/delete akcijama ili sirem workflowu.

No-Go za:

- clinical approval
- readiness clearance
- override workflow
- Task engine
- Outcome Evidence
- appointment status change
- patient messaging
- edit/delete snapshot
- supersession UI bez posebnog contracta

## Recommended next task

`Program 1 Phase B19 - Snapshot Detail Read-Only View`
