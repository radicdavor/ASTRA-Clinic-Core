# Clinical Documentation Reliability — Phase C draft and concurrency

## Draft state

The clinical form distinguishes the server snapshot from the local working copy.

- **Nespremljene promjene** appears when they differ.
- **Spremi skicu** sends the local values with the expected instance and revision.
- **Skica spremljena** appears only after the server accepts the new revision.
- **Obrazac dovršen** appears only after atomic completion succeeds.
- Existing form instances load automatically when an activity is selected.

The mobile action row is sticky and keeps the current primary action and draft save available without scrolling to the end of a long form.

## Navigation safety

A dirty form protects:

- activity switching in the journey activity rail;
- stage switching in the journey workspace;
- internal route links;
- browser unload/refresh.

The controlled application dialog offers **Ostani**, **Odbaci i nastavi**, and **Spremi skicu i nastavi**. No browser-native confirmation is used by this clinical form flow.

## Optimistic concurrency

Every draft PATCH and completion request includes:

- `expected_instance_id`;
- `expected_revision_number`.

The server obtains a row lock and compares the active instance and current revision. A stale request receives HTTP 409 and cannot overwrite newer data. The response includes the current revision, update timestamp and server data.

The conflict panel:

- leaves the clinician's local text visible;
- names the conflict in Croatian;
- offers a field-by-field comparison;
- permits explicit reload of the server version;
- never automatically merges clinical text.

## Regression coverage

Frontend tests cover immediate completion, retained data after validation failure, invalid-field focus, draft state, stale-version conflict, and protected activity switching. Backend tests simulate two clients, assert that the second stale write receives 409, and verify the first saved values remain authoritative.

Phase C is implemented. Full track closure remains prohibited until Phases D–K are revalidated and all closure conditions pass.
