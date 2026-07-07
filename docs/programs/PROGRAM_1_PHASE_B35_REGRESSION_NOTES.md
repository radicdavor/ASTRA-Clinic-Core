# Program 1 Phase B35 - Regression Notes

Status: snapshot restore consistency regression coverage

## Implemented

B35 adds practical restore-consistency regression coverage without implementing a real dump/restore workflow.

Implemented backend test proves:

- capture snapshot exists
- supersession snapshot exists
- old snapshot points to new snapshot
- old snapshot copied payload remains unchanged
- original capture reason remains unchanged
- idempotency key/fingerprint remain preserved
- capture audit event references the captured snapshot
- supersession audit event references old and new snapshots
- replacement snapshot exists
- DB invariant blocks post-restore-style protected mutation attempt

## Not Implemented

B35 did not implement:

- real backup automation
- real restore automation
- production backup SLA
- new endpoint
- new frontend UI
- clinical approval
- readiness clearance
- Outcome Evidence
- Task engine

## Tests Run

- `docker compose build backend`
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_snapshots.py`: 63 passed

## Recommended Next Task

`Program 1 Phase B36 - Snapshot Permission UX and Error Wording Review`
