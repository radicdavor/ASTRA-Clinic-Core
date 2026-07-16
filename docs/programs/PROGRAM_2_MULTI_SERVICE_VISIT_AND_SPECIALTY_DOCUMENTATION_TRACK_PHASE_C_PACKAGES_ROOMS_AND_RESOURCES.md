# Program 2 Multi-Service Visit Track — Phase C

## Packages, rooms and resources

Status: domain foundation implemented; package-management UI and publishing workflow remain pending.

## Package model

The additive `0047_multi_service` migration introduces:

- `ServicePackage` — stable catalog identity;
- `ServicePackageVersion` — immutable version boundary with draft/publishing metadata;
- `ServicePackageItem` — ordered service/activity definition, duration, relative offset, dependency, preferred clinic/room type, preparation metadata, and billing inclusion rule.

Package items are definitions only. Applying a package will create ordinary `JourneyActivity` and `Appointment` records so the operational workflow has one canonical representation. Runtime activities must not depend on a mutable package draft.

## Scheduling rules now enforced

- all activities share the anchor date;
- each activity has its own clinician and room;
- clinician working hours are reused from the existing scheduling service;
- clinician and room conflicts are rejected;
- service/room suitability and clinic alignment reuse existing scheduling rules;
- patient overlap is now rejected explicitly;
- activity dependencies must reference an activity in the same journey.

## Deliberate constraints

- Provider-to-multiple-clinic availability is not inferred. The current provider/clinic ownership rule remains authoritative until a separate connected-clinic availability model is approved.
- Package application, draft approval, immutable published versions, activity participants, and package editor UI are not yet exposed. The tables are present so those capabilities can be added without replacing the activity model.
- No package may approve preparation, select a clinical diagnosis, or mark an activity ready without human-owned prerequisite resolution.

## API foundation

- `GET /api/patient-journeys/{journey_id}/activities`
- `POST /api/patient-journeys/{journey_id}/activities`
- `POST /api/patient-journeys/{journey_id}/activities/{activity_id}/transition`

Creation requires appointment-write permission. Reading uses journey-read permission. Status transitions use journey-transition permission. All mutations are audited.

