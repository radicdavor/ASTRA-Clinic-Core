# Program 1 Phase G10 - Timeline Read API Error Permission UX Contract

Safe error states:

- unauthenticated: login required
- permission denied: timeline read permission missing
- patient not found: patient-scoped resource unavailable
- invalid filter: request parameter invalid
- empty timeline: no source-linked timeline events to show
- backend unavailable: timeline cannot currently be loaded

Forbidden wording:

- diagnosis failed
- treatment blocked
- clearance denied
- approval denied
- patient unsafe
- issue resolved

No error state implies clinical decision, workflow enforcement or patient status change.

