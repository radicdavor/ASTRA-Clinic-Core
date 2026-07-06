## Summary

- 

## Architecture Bible Check

- [ ] I read `docs/ASTRA_ARCHITECTURE_BIBLE.md`.
- [ ] This change aligns with ASTRA's philosophy.
- [ ] This change makes the system simpler or safer, not only larger.
- [ ] This change fits inside the current Clinic Core model.
- [ ] This change preserves the shared language: Patient, Appointment, Service, Invoice, Audit.
- [ ] This change preserves security, audit and AI boundaries.

If any item is unchecked, explain why the change should still proceed:

## Safety

- [ ] No real patient data is enabled.
- [ ] No real Croatian fiscalization is implied.
- [ ] Critical actions remain warned, confirmed and audited.
- [ ] AI behavior, if any, is assistive and clearly labeled.

## Tests

- [ ] Backend tests pass.
- [ ] Frontend typecheck/build or smoke checks pass.
- [ ] Documentation updated if workflow language changed.

