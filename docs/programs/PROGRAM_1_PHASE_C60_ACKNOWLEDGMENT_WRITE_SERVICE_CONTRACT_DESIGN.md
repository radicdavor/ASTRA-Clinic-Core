# Program 1 Phase C60 - Acknowledgment Write Service Contract Design

Status: service-contract design

## Svrha

C60 definira buduci interni write service za Human Review Acknowledgment.

Ovaj dokument ne odobrava endpoint, UI akciju, permission seed, produkcijsku uporabu ili stvarne podatke pacijenata.

Acknowledgment znaci samo da je covjek pregledao advisory signal ili snapshot context. Ne znaci clinical approval, readiness clearance, override, Outcome Evidence, Task ili promjenu statusa termina.

## Predlozena interna funkcija

Predlozeni interni service naziv:

`create_clinical_readiness_review_acknowledgment(...)`

Predlozeni modul:

`backend/app/services/clinical_readiness_acknowledgments.py`

Service ostaje internal-only dok se zasebno ne odobri endpoint contract, permission model i UI safety review.

## Ulazi

Minimalni ulazi:

- `db`
- `appointment_id`
- `patient_id`
- `advisory_signal_key`
- `actor_user_id`
- `actor_role`
- `reason`

Opcionalni ulazi:

- `snapshot_id`
- `request_id`
- buduci `idempotency_key`, ako se storage eksplicitno implementira kasnije

Service ne smije primati approval, clearance, override, appointment status, Task, Outcome Evidence ili patient message payload.

## Izlaz

Izlaz je spremljeni `ClinicalReadinessReviewAcknowledgment` red.

Izlaz ne smije sadrzavati polja koja impliciraju odluku:

- `approval_status`
- `clearance_status`
- `override_status`
- `task_id`
- `outcome_evidence_id`
- `appointment_status`
- `patient_message_id`

## Validacijske odgovornosti

Service mora provjeriti:

- `reason` je obavezan i nije whitespace
- `actor_user_id` je obavezan
- `actor_role` je obavezan i ne predstavlja API key ili system job
- appointment postoji
- appointment pripada navedenom patientu
- `advisory_signal_key` je obavezan
- ako je `snapshot_id` naveden, snapshot postoji i pripada istom appointmentu i patientu

Ako validacija padne, service mora odbiti insert i audit.

## Transaction Boundary

Acknowledgment insert i audit write moraju biti u istoj transakciji.

Redoslijed:

1. validacija ulaza
2. ucitavanje appointment/patient/snapshot konteksta
3. insert acknowledgment reda
4. audit write u istoj sesiji
5. jedan commit

Ako insert ili audit write padne, transakcija se rollbacka.

## Audit Requirement

Buduci audit event mora zapisati:

- acknowledgment id
- appointment id
- patient id
- advisory signal key
- snapshot id, ako postoji
- actor user id
- actor role
- reason
- limitations
- request id, ako postoji

Audit ne smije implicirati approval, clearance, override, task completion ili outcome.

## No Workflow Side Effects

Service ne smije:

- mijenjati appointment status
- stvarati Task
- stvarati Outcome Evidence
- stvarati ClinicalPlan
- stvarati ClinicalEpisode
- slati patient message
- mijenjati snapshot payload
- mijenjati advisory signal u clinical decision

## Zasto jos nema endpointa

Endpoint ostaje no-go dok nisu odvojeno stabilizirani:

- permission boundary
- user-facing reason UX
- idempotency storage
- audit review workflow
- production/real-data governance

Interni service, ako se implementira, ne znaci runtime rollout.

