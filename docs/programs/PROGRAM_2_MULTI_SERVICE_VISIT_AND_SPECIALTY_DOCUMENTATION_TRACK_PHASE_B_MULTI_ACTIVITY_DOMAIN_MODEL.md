# Program 2 Multi-Service Visit Track — Phase B

## Multi-activity domain model

Status: implemented and migration-tested.

## Canonical ownership

- `PatientJourney` remains the single aggregate for one physical patient arrival.
- The existing `PatientJourney.appointment_id` remains the primary/anchor compatibility field.
- `JourneyActivity` represents one consultation, examination, procedure, or treatment within that arrival.
- Every journey has at least one activity. Migration `0047_multi_service` backfills the primary activity from the anchor appointment.
- Additional activities receive their own `Appointment`, but never another `PatientJourney`.
- An appointment can belong to at most one activity, and an activity belongs to exactly one journey.
- All activities in one journey must belong to the journey patient and the anchor date.

## Activity contract

An activity records service, specialty, clinician, room, clinic, order, dependency, planned/actual time, form resolution, consumables, billing and explicit lifecycle status.

Allowed lifecycle:

`planned → ready → in_progress → completed`

The explicit terminal alternatives are `not_performed` and `cancelled`. They require a human-entered reason. Invalid and backwards transitions are rejected and all accepted transitions create both an audit record and a journey event.

## Compatibility and migration

- Existing journeys are preserved without ID changes.
- Existing encounters are linked to their backfilled primary activity.
- The former one-encounter-per-journey database uniqueness is removed; activity uniqueness is the future source of encounter ownership.
- Legacy form state is marked `legacy`; it is not represented as a newly completed form.
- New single-service journeys create their primary activity atomically with the journey.

## Safety rules

- An activity cannot be added to a completed, cancelled, or no-show journey.
- A second date is rejected because it represents another arrival.
- Patient, clinician, and room overlap are rejected by scheduling validation.
- Activity start requires completed reception check-in, assigned clinician and room, resolved form requirements, and a completed dependency when one exists.
- No transition makes a clinical decision or resolves a clinical blocker automatically.

## Verification evidence

- Empty PostgreSQL database: upgrade through `0047_multi_service` passed.
- Downgrade `0047 → 0046` and re-upgrade passed.
- Representative development database: 48 journeys produced 48 primary activities; zero existing encounters were left without an activity.
- Targeted backend suite: 30 tests passed, including three sequential services in one arrival, overlap rejection, explicit transition, and legacy journey behavior.

