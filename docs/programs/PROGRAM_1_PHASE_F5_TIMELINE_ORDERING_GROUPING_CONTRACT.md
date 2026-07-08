# Program 1 Phase F5 - Timeline Ordering Grouping Contract

Status: documented

## Ordering

Use clinical/event timestamp when safely available. Fall back to source object `created_at`, then stable id ordering. Display timestamp and created timestamp should remain distinguishable.

## Grouping

Future UI may group by date, source document, clinical domain or source object type. Missing dates should be explicitly labeled rather than silently promoted or hidden.

## Supersession and Corrections

Corrected and superseded items remain additive. Timeline ordering must not rewrite old source payloads.

## Safety Boundary

Ordering is not clinical priority, workflow enforcement, triage, diagnosis or treatment recommendation unless a later explicit phase approves that behavior.
