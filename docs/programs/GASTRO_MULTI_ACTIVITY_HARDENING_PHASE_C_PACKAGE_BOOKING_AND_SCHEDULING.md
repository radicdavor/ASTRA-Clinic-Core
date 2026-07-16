# Phase C — Package booking and scheduling

Reception uses `/appointments/package` to select a patient, published package, date, start time, clinician, and room for every ordered activity.

`POST /api/service-package-versions/{id}/schedule-preview` is non-mutating. It validates patient, assignments, duration, provider conflicts, room conflicts, patient overlap, service/room compatibility, one-date arrival semantics, and one-clinic coordination. It returns per-activity conflicts, warnings, and total visit duration.

`POST /api/service-package-versions/{id}/book` creates the appointment, one `PatientJourney`, and all `JourneyActivity` rows in one transaction. A unique `package_booking_key` makes safe client retries return the original coordinated arrival instead of duplicating it. The UI uses an application confirmation modal and never `window.confirm`.

