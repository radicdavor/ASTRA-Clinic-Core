# V5 Implementation

V5 closes hardening gaps left after the V4 sprint.

Implemented:

- appointment material consumption moved from route code into `app.services.appointment_materials`
- material consumption validates all requested stock before mutating any batch
- appointment completion with insufficient second material leaves appointment status and stock unchanged
- appointment update conflict validation is covered by tests
- appointment update audit snapshots are covered by tests
- `SECURITY.md` documents the minimum production security baseline

This sprint intentionally avoids new medical modules, fiscalization and external integrations.
