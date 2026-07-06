# Reception And Resource Scheduling

Status: MVP implemented foundation

## Purpose

Reception gives clinic staff a resource-aware view of the day.

It shows who is scheduled, which service is planned, which provider and room are assigned, and whether the patient has arrived.

## User Roles

Reception is useful for:

- reception staff
- nurses
- physicians
- administrators

The MVP uses existing appointment permissions. Future role-specific reception permissions may be added later.

## Slot Logic

The daily reception view uses 10-minute slots from 07:00 to 21:00.

Appointment cards appear at the appointment start time and span multiple slots according to appointment duration.

Empty slots remain visible.

Weekly and monthly views are shown as deferred toggles in the UI. The active scheduling grid is daily.

## Conflict Rules

Appointment create/update validates:

- provider overlap
- room overlap
- provider cannot work in two rooms at the same time
- service-room compatibility
- provider and room clinic compatibility
- appointment start/end duration
- service duration match

Conflicts return `409`.

## Arrival Workflow

Reception can open an appointment from the grid and:

- review patient identity
- complete missing patient data
- mark the appointment as arrived
- start service
- open Appointment Workspace
- open Patient Workspace

Marking arrived:

- sets appointment status to `arrived`
- stores `arrived_at`
- stores identity verification timestamp when confirmed
- writes audit

## Room, Service And Provider Compatibility

The MVP adds:

- `Clinic`
- provider `staff_role`
- provider `clinic_id`
- room `clinic_id`
- room allowed services

Seed data creates Gastroenterologija and Estetika clinics and assigns existing demo rooms/providers.

## Readiness

Readiness warns about:

- rooms without allowed services
- services without allowed rooms
- providers without clinic assignment
- today's appointments without basic resource context

These are operational warnings or blockers depending severity.

## Deferred

- full weekly grid
- full monthly grid
- multi-clinic staff rota
- provider working hours
- nurse/support staff assignment per service
- drag-and-drop rescheduling
- real production patient data
- Workflow Engine
- Knowledge Engine
- Episode Engine promotion
