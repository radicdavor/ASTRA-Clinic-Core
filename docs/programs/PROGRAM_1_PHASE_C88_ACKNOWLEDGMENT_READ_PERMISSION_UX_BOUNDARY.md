# Program 1 Phase C88 - Acknowledgment Read Permission UX Boundary

Status: permission UX boundary

## Safe Permission Wording

Approved wording:

- `Nemate dozvolu za prikaz zapisa ljudskog pregleda savjetodavnih signala.`
- `Ovo ne mijenja status termina.`
- `Za klinicku interpretaciju potreban je ljudski pregled.`

## Forbidden Wording

Do not use:

- clearance denied
- approval denied
- override denied
- blocked
- patient not ready
- pacijent spreman
- postupak odobren

## Runtime Behavior

Permission denied is local to the acknowledgment panel.

It must not hide:

- Clinical Readiness Preview
- Savjetodavni signali
- Snapshot history
- appointment operational details

## Implemented UI Boundary

Appointment Workspace uses safe permission wording and keeps the section non-blocking.

