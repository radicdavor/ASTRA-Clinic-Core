# PR #3 Second Security Rescan — Affected Surface

Scanned revision: `ec638e9030f17186043ef779079714c4c31906d0`

Scan: `99e0dad5-e557-4f08-91ab-d4a49b57588f`

This inventory records the scheduling and security-audit surfaces reviewed
before remediation. It does not reproduce exploit instructions or clinical
content.

## Scheduling projections

| Route or surface | Permission / actor | Episode reference | Previous projection | Risk | Required projection |
| --- | --- | --- | --- | --- | --- |
| `POST /api/appointments` | `appointments.write`, clinic user | accepted | `AppointmentOut` with `ClinicalEpisodeOut` | mixed/unsafe | operational |
| `POST /api/intake/web/appointments` | `journey.create`, clinic user | accepted | `AppointmentOut` with `ClinicalEpisodeOut` | mixed/unsafe | operational |
| `POST /api/ai/appointments/create` | `ai.appointments.create`, tenant actor/API key | accepted | `AppointmentOut` with `ClinicalEpisodeOut` | mixed/unsafe | operational |
| `GET /api/appointments` | `appointments.read`, clinic user | returned | broad `AppointmentOut` | mixed/unsafe | operational |
| `GET /api/appointments/{id}` | `appointments.read`, clinic user | returned | broad `AppointmentOut` | mixed/unsafe | operational |
| `PATCH /api/appointments/{id}` | `appointments.write`, clinic user | accepted/returned | broad `AppointmentOut` | mixed/unsafe | operational |
| `GET /api/schedule/day` | `appointments.read`, clinic user | returned | broad `AppointmentOut` | mixed/unsafe | operational |
| reception arrival/start | reception clinic permissions | returned | broad `AppointmentOut` | mixed/unsafe | operational |
| patient-journey nested appointment | journey permissions | returned | broad `AppointmentOut` | mixed/unsafe | operational |
| episode read endpoints | medical category plus institution clinical scope | explicit clinical read | `ClinicalEpisodeOut` | clinical-authorized | clinical |
| package booking | service-package scheduling permission | accepted by shared helper | journey projection | operational | opaque reference only |

The canonical rule is that scheduling authority never implies clinical-read
authority. `episode_id` is an opaque linkage value. Clinical content is
retrieved only from an explicit clinical endpoint using the shared medical
category and institution-scope checks.

## Appointment creation and linkage

All manual, web, AI and package creation paths converge on
`create_appointment_with_journey`. Episode linkage is therefore resolved by one
service function using the final tuple:

`episode.id + episode.patient_id + episode.institution_id`

The resolver returns one generic not-found result for missing, mismatched,
foreign or unresolved references. It does not serialize clinical data.

## Security audit producers

| Action | Producer | Previous persistence | Remediated policy |
| --- | --- | --- | --- |
| `auth.browser_login_success` | successful browser login | individual | individual |
| `auth.browser_logout` | browser logout | individual | individual |
| `auth.browser_session_revoked` | administrative/session lifecycle revocation | individual | individual |
| `auth.browser_session_invalid` | invalid browser-session rejection | bounded only for anonymous unresolved sessions | bounded counter for all actor states |
| `auth.browser_csrf_invalid` | session-bound CSRF rejection | individual rows | bounded counter |
| `auth.browser_credential_conflict` | conflicting browser/API credentials | individual rows | bounded counter |

The static policy registry classifies every browser security event and owns
persistence mode, aggregation window, retention and actor-key behavior.
Unknown actions fail closed. Aggregation uses only safe finite dimensions and
resolved internal actor identifiers.

## Clinical access events

The following direct assertions represent clinical content access and require
the canonical `medical_staff` professional category before object resolution:

- `clinical_workspace.opened`
- `clinical_form.viewed`
- `signed_report.viewed`
- `source_document.viewed`
- `source_document.downloaded`
- `clinical_report.printed`

Operational patient, billing and audit-view events retain their existing
permission and scope rules.

## Variant disposition

- `ClinicalEpisodeOut`: safe only on explicit clinical routes.
- `AppointmentOut`: remediated as an operational projection without embedded
  episode content.
- `AppointmentOperationalOut`: canonical scheduling response.
- package and activity creation: safe through the shared episode-reference
  resolver and operational journey projection.
- request IDs: remediated at HTTP ingress and defensively normalized again at
  independent audit persistence.
- unrelated clinical, signed-report, billing and recovery modules: not changed.
