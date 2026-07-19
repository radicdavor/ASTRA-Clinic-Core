# Phase E - Package booking and activity preparation

Status: implemented inside the existing Program 2 gastro workflow.

Reception uses `/appointments/package` for one coordinated package arrival. The UI selects the patient, published package, date, ordered activities, physicians, rooms, preview, and final confirmation through an application modal.

`POST /api/service-package-versions/{id}/schedule-preview` is non-mutating. It returns proposed activities, total duration, per-activity conflicts, room/provider/patient overlap validation, same-day one-arrival checks, clinic warnings, preparation requirements, and package warnings.

`POST /api/service-package-versions/{id}/book` creates one `PatientJourney`, one anchor appointment, and one `JourneyActivity` per package item in one transaction. The `package_booking_key` makes retry behavior idempotent and prevents duplicate coordinated arrivals.

Activity-specific preparation is stored in `ActivityPreparationRequirement`. Requirements retain activity provenance and are aggregated into one visit-level preparation plan. Contradictory canonical requirement keys produce an open clinical blocker instead of silently merging free text.

Clinical review categories such as medication, anticoagulant, antiplatelet, and diabetes review cannot be administratively confirmed without the clinical-review permission.

No public web booking, live AI secretary, live e-mail, SMS, or production scheduling integration is authorized by this phase.
