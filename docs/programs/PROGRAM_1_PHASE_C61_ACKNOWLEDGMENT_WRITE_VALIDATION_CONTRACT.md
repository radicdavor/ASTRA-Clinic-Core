# Program 1 Phase C61 - Acknowledgment Write Validation Contract

Status: validation contract

## Svrha

C61 definira siguran validation/error model za buduci interni Human Review Acknowledgment write service.

Ovaj dokument ne uvodi endpoint, permission seed, frontend action ili runtime rollout.

## Validation Matrix

| Scenario | Validation point | Proposed error | Safe message | Audit implication | Rollback expectation |
| --- | --- | --- | --- | --- | --- |
| Missing reason | before DB insert | `ValueError` | `Razlog pregleda signala je obavezan` | no audit | rollback/no insert |
| Missing actor | before DB insert | `ValueError` | `Actor user id je obavezan` | no audit | rollback/no insert |
| Invalid appointment | appointment load | `LookupError` | `Termin nije pronaden` | no audit | rollback/no insert |
| Patient mismatch | appointment/patient scope check | `ValueError` | `Termin ne pripada navedenom pacijentu` | no audit | rollback/no insert |
| Unknown advisory signal | advisory key validation | `ValueError` | `Advisory signal nije prepoznat u ovom kontekstu` | no audit | rollback/no insert |
| Stale advisory signal | future freshness check | `ValueError` | `Advisory signal vise nije aktualan` | optional blocked audit only after separate contract | rollback/no insert |
| Invalid snapshot reference | snapshot load | `LookupError` | `Snapshot nije pronaden` | no audit | rollback/no insert |
| Snapshot appointment mismatch | snapshot scope check | `ValueError` | `Snapshot ne pripada ovom terminu` | no audit | rollback/no insert |
| Duplicate acknowledgment | future idempotency or uniqueness check | conflict-style error | `Acknowledgment je vec zapisan za isti kontekst` | no second audit | rollback/no second insert |
| Unsupported actor type | actor boundary check | `PermissionError` | `Acknowledgment zahtijeva prijavljenog korisnika` | no audit | rollback/no insert |
| API key denial | actor boundary check | `PermissionError` | `API key ne smije zapisati acknowledgment` | no audit | rollback/no insert |
| System job denial | actor boundary check | `PermissionError` | `System job ne smije zapisati acknowledgment` | no audit | rollback/no insert |
| No workflow side effect | post-write invariant | test failure / rollback on runtime bug | `Acknowledgment ne mijenja workflow stanje` | audit remains review-only | rollback if same transaction detects mutation |

## Safe Error Style

Messages must describe validation failure without implying:

- patient is ready
- procedure is approved
- readiness is cleared
- override was accepted
- issue was resolved

## Audit Boundary

Validation failures do not write the normal acknowledgment audit event.

If future governance wants blocked-attempt audit, that must be a separate event and must not share the success event name.

## Runtime Boundary

C61 does not implement route behavior.

Endpoint mapping of these errors remains future work.

