# Program 1 Phase B36 - Regression Notes

Status: snapshot permission UX and error wording review

## Implemented

B36 stabilizes user-facing snapshot permission and safety wording.

Updated:

- capture permission denied wording
- capture save error wording
- supersession permission denied wording
- capture modal helper text
- supersession modal helper text
- frontend smoke assertions

## Safety Wording Preserved

UI now states:

- snapshot is a saved preview record
- snapshot is not clinical approval
- snapshot does not change appointment status
- snapshot does not message patients
- supersession does not change old content

## Not Implemented

B36 did not implement:

- new UI actions
- new endpoint
- approval
- clearance
- override
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging

## Tests Run

- `npm run typecheck`
- `npm run build`
- `npm run smoke`

## Recommended Next Task

`Program 1 Phase B37 - Snapshot CI Gate Documentation and Script Review`
