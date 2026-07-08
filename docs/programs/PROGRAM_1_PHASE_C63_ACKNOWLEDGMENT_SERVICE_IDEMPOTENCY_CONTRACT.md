# Program 1 Phase C63 - Acknowledgment Service Idempotency Contract

Status: idempotency contract

## Svrha

C63 definira buduce idempotency/retry ponasanje za Human Review Acknowledgment write service.

Ovaj dokument ne dodaje idempotency storage i ne uvodi endpoint.

## Buduci Key

Predlozeni input:

- `idempotency_key`

Predlozeni transport za buduci endpoint:

- request body field ili `Idempotency-Key` header

Izbor transporta ostaje otvoren do endpoint implementacije.

## Fingerprint Inputs

Predlozeni fingerprint mora ukljuciti:

- appointment id
- patient id
- advisory signal key
- snapshot id, ako postoji
- actor user id
- cleaned reason
- acknowledgment schema version

Fingerprint ne smije ukljuciti client-sent advisory payload kao source truth.

## Same Key / Same Fingerprint

Ako isti actor ponovi isti key i isti fingerprint:

- vratiti isti acknowledgment
- ne stvoriti drugi red
- ne napisati drugi audit event

## Same Key / Different Fingerprint

Ako isti key ima drugi fingerprint:

- vratiti conflict-style error
- ne stvoriti drugi red
- ne napisati success audit event

## Duplicate Reason / Duplicate Advisory Signal

Isti reason ili isti advisory signal sam po sebi nije dovoljan za idempotency.

Bez idempotency keya, buduci runtime mora imati odvojenu politiku protiv slucajnog dupliranja ako je potrebna.

## Storage Expectations

Trenutna DB foundation ne sadrzi idempotency columns za acknowledgment.

Zato idempotency storage ostaje deferred.

Ako se implementira kasnije, predlozena nullable polja su:

- `idempotency_key`
- `idempotency_fingerprint`

Uz indeks koji ukljucuje:

- `appointment_id`
- `actor_user_id`
- `idempotency_key`

## Audit Prevention

Idempotent retry ne smije stvoriti drugi audit event.

Conflict ne smije stvoriti success audit event.

## Zakljucak

Service moze postojati bez idempotency storage samo kao internal-only prototip. Runtime endpoint rollout mora ponovno rijesiti idempotency.

