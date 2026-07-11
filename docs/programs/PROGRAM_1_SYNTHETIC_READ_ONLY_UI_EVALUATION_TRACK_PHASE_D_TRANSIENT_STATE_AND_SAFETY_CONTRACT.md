# Program 1 Phase D - Transient State and Safety Contract

## State Model

The runner keeps only React in-memory state for the current browser tab:

- six preflight checkbox states
- one status for each of eight tasks
- one stop-state boolean

Allowed task statuses:

- `not-reviewed`
- `completed`
- `assistance-needed`

These labels describe a transient moderator walkthrough. They are not controlled evidence and are erased by reset, refresh, navigation, or tab closure.

## Gating Rules

- tasks remain hidden and locked until all six preflight items are checked
- a missing preflight confirmation immediately prevents task access
- stop state disables preflight changes and all task status controls
- stop state displays a `role=alert` instruction
- reset clears every checkbox, task status, and stop state
- reset never creates, stores, exports, or restores a record

## Safety Copy

The route permanently states:

- local synthetic evaluation
- not for clinical use
- do not enter or speak real patient information
- progress exists only in tab memory
- transient progress is not proof of a completed session

## Evidence Boundary

Controlled eligibility, consent, observations, quotes, severity classification, deviations, and final decisions remain in the Phase C controlled templates. The runner intentionally has no free-text or evidence capture field.

