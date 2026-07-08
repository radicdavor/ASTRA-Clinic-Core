# Program 1 Phase J4 - Role-Based Demo Walkthrough

## Physician

May view source-linked clinical context. Must not treat read-only events as diagnosis, treatment, approval or clearance.

## Nurse

May observe safe read-only context according to demo role policy. Must not interpret review/readiness as a final clinical decision.

## Receptionist/Admin

May observe operational context and demo navigation. Must not enter real patient data or present clinical surfaces as decision support.

## Technical Operator

May run Docker, reset demo state, validate tests and stop the demo on safety issues.

## Observer/Stakeholder

May watch the demo and ask questions. Must be told that this is not production, not real-data approved and not certified clinical software.
