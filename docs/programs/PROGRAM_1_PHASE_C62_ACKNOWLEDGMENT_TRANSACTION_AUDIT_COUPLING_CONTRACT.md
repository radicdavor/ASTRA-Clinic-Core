# Program 1 Phase C62 - Acknowledgment Transaction Audit Coupling Contract

Status: transaction/audit contract

## Svrha

C62 definira atomsku vezu izmedu acknowledgment DB inserta i audit zapisa.

Acknowledgment je review record, ne clinical decision.

## Transaction Rule

Acknowledgment row insert i audit write moraju se dogoditi u istoj database transakciji.

Nije dopusteno:

- commitati acknowledgment pa tek kasnije audit
- zapisati audit bez acknowledgment reda
- zapisati acknowledgment bez audit eventa
- mijenjati appointment status u istoj transakciji

## Minimal Audit Payload

Buduci audit payload mora sadrzavati:

- `acknowledgment_id`
- `appointment_id`
- `patient_id`
- `advisory_signal_key`
- `snapshot_id`, ako postoji
- `actor_user_id`
- `actor_role`
- `reason`
- `limitations`
- `schema_version`
- `request_id`, ako postoji
- `is_decision=false`
- `is_clearance=false`
- `is_override=false`

## Rollback Rules

Ako DB insert padne:

- audit se ne pise
- nema djelomicnog zapisa

Ako audit write padne:

- acknowledgment insert se rollbacka
- nema orphan review reda

Ako commit padne:

- caller mora dobiti exception
- stanje mora ostati bez djelomicnog workflow side effecta

## Request Id Handling

Ako request id postoji u caller kontekstu, treba ga prenijeti u audit zapis.

Ako service radi bez request konteksta, request id moze ostati `null`.

## Zabranjene Veze

Audit payload ne smije sadrzavati:

- Outcome Evidence id
- Task id
- appointment status mutation
- patient message id
- approval status
- clearance status
- override status

## Zakljucak

Audit je dokaz da je human review acknowledgment zapisan. Audit nije Outcome Evidence i nije odobrenje postupka.

