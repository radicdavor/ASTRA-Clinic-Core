# Program 1 Phase B11 - Snapshot Capture Endpoint Design

Status: documentation-only endpoint design

## 1. Svrha

B11 definira buduci capture endpoint za Clinical Readiness Snapshot prije implementacije.

Ovaj dokument ne implementira:

- backend rutu
- frontend UI
- DB model
- Alembic migraciju
- runtime persistence
- audit event
- snapshot history UI
- Outcome Evidence
- Task engine
- override
- promjenu appointment statusa

Svrha je definirati API contract, permissions, transaction boundary i sigurnosne granice prije pisanja koda.

## 2. Buduci capture endpoint

Predlozena HTTP metoda:

`POST`

Predlozena ruta:

`/api/appointments/{appointment_id}/clinical-readiness-snapshots`

Razlog:

- Clinical Readiness Preview je appointment-scoped.
- Snapshot nastaje iz previewa za konkretni appointment.
- Ruta jasno razlikuje snapshot capture od read-only preview endpointa.

Postojeci preview endpoint ostaje:

`GET /api/appointments/{appointment_id}/clinical-readiness-preview`

Capture endpoint se ne implementira u B11.

## 3. Tko smije captureati snapshot

Buduca pravila:

- physician smije captureati clinical-context snapshot
- nurse/admin smiju captureati samo ako buduci governance eksplicitno dopusti operational preview snapshot
- AI ne smije captureati snapshot
- API key/agent ne smije captureati snapshot bez posebnog, minimalnog scopea i maintainer odluke
- system ne smije auto-captureati snapshot na page load

Preporucena buduca permission:

`clinical_readiness.snapshots.write`

Preporucena read permission za history:

`clinical_readiness.snapshots.read`

Default:

Ako permission ili uloga nisu jasni, capture nije dopusten.

## 4. Ulazni parametri

Path:

- `appointment_id`

Body:

```json
{
  "reason": "Pilot review prije kolonoskopije.",
  "client_preview_generated_at": "2026-07-07T10:30:00Z",
  "idempotency_key": "optional-client-generated-key"
}
```

Obavezno:

- `reason`

Opcionalno:

- `client_preview_generated_at`
- `idempotency_key`

Server ne smije vjerovati klijentskom preview payloadu kao source of truth.

Server treba u trenutku capturea ponovno izgraditi preview i spremiti ono sto je server prikazao/izracunao u tom trenutku.

## 5. Izlazni response shape

Konceptualni response:

```json
{
  "id": 1,
  "appointment_id": 10,
  "patient_id": 20,
  "service_id": 30,
  "created_at": "2026-07-07T10:31:00Z",
  "created_by_user_id": 5,
  "schema_version": "clinical-readiness-snapshot-v1",
  "preview_generated_at": "2026-07-07T10:31:00Z",
  "preview_status": "ready_with_warning",
  "template_key": "colonoscopy",
  "template_label": "Kolonoskopija",
  "template_version": "demo-v1",
  "template_binding_status": "explicit",
  "is_preview_snapshot": true,
  "snapshot_reason": "Pilot review prije kolonoskopije.",
  "disclaimer": "Snapshot je zapis preview prikaza, ne clinical approval.",
  "items_json": [],
  "limitations_json": [],
  "source_warnings_json": [],
  "source_refs_json": []
}
```

Response mora ostati jasno preview-only.

Ne smije vratiti polja poput:

- `approved`
- `cleared`
- `procedure_allowed`
- `task_created`
- `outcome_evidence_id`

## 6. Error states

Buduci endpoint treba vratiti sigurne error states:

- `401 Unauthorized` ako korisnik nije prijavljen
- `403 Forbidden` ako korisnik nema permission
- `404 Not Found` ako appointment ne postoji
- `409 Conflict` ako idempotency key vec postoji s drugim payloadom
- `422 Unprocessable Entity` ako nedostaje razlog ili appointment nema minimalni kontekst
- `423 Locked` ili `409 Conflict` samo ako buduci governance uvede zakljucavanje capturea, ne za clinical approval

Error poruke ne smiju implicirati da je pacijent clinical ready ili not ready.

## 7. Idempotency odluka

Preporuka:

Capture endpoint treba podrzati opcionalni `idempotency_key`.

Razlog:

- korisnik moze dvaput kliknuti capture
- mreza moze ponoviti request
- ne zelimo slucajne duple snapshotove za isti eksplicitni capture

Pravila:

- isti user + appointment + idempotency key vraca isti snapshot ako je request ekvivalentan
- isti key s drugim reasonom ili kontekstom vraca conflict
- ako key nije poslan, svaki eksplicitni capture moze stvoriti novi snapshot

Idempotency ne smije sakriti stvarni novi capture ako korisnik namjerno zeli novi snapshot.

## 8. Transaction boundary

Buduci capture mora biti jedna transakcija:

1. ucitati appointment
2. validirati permission i kontekst
3. izgraditi server-side preview
4. kopirati preview content u snapshot payload
5. spremiti snapshot
6. napisati audit event
7. commit

Ako audit write ne uspije, snapshot capture ne smije biti smatran uspjesnim.

Ako snapshot save ne uspije, audit event ne smije ostati kao lazni capture.

Capture ne smije u istoj transakciji mijenjati appointment status, taskove, ClinicalPlan, ClinicalEpisode ili Outcome Evidence.

## 9. Buduci audit event

Buduci audit event:

`clinical_readiness_snapshot_captured`

Audit payload treba sadrzavati:

- snapshot id
- appointment id
- patient id
- service id
- template key
- template version
- preview status
- item count
- limitation count
- capture reason
- actor

Audit event znaci:

`Korisnik je spremio snapshot preview prikaza.`

Audit event ne znaci:

- procedure approved
- patient cleared
- physician confirmed readiness
- override accepted
- outcome documented

## 10. Sigurnosne napomene

Capture endpoint mora:

- zahtijevati authenticated user
- zahtijevati reason
- spremiti preview-only disclaimer
- spremiti immutable copied payload
- pisati audit event
- ostati appointment-scoped
- koristiti samo reviewed/source-linked clinical knowledge kao official source
- izbjeci Patient Clinical Summary kao source truth
- izbjeci unreviewed AI kao official source

Capture endpoint ne smije:

- raditi clinical approval
- clearati readiness
- napraviti override
- kreirati task
- kreirati Outcome Evidence
- kreirati ClinicalPlan
- kreirati ClinicalEpisode
- promijeniti appointment status
- slati poruku pacijentu
- sakriti limitations

## 11. Odnos prema preview endpointu

Preview endpoint:

`GET /api/appointments/{appointment_id}/clinical-readiness-preview`

- read-only
- live calculation
- ne persistira snapshot
- ne pise audit za obican read

Capture endpoint:

`POST /api/appointments/{appointment_id}/clinical-readiness-snapshots`

- eksplicitna write akcija
- zahtijeva razlog
- sprema immutable copy live previewa
- pise audit event

Capture sprema ono sto preview prikaze u trenutku capturea.

Ne sprema ono sto je korisnikov browser mozda ranije vidio ako se server-side preview u medjuvremenu promijenio.

Ako je potrebna stroga usporedba s ranije prikazanim previewom, buduci endpoint moze koristiti `client_preview_generated_at` samo kao upozorenje ili conflict signal, ne kao izvor payloada.

## 12. UI implikacije za buduci snapshot history

Buduci Appointment Workspace moze imati snapshot history sekciju tek nakon implementacije persistencea.

UI mora prikazati:

- timestamp capturea
- tko je captureao snapshot
- reason
- preview status
- template key/version
- binding status
- limitations
- preview-only disclaimer
- link na audit event ako postoji

UI ne smije prikazati:

- `Mark ready`
- `AI cleared`
- `Procedure approved`
- `Outcome Evidence`
- `Task created`
- `Override accepted`

Capture button smije postojati samo ako:

- governance je implementiran
- permission postoji
- reason input postoji
- audit event postoji
- regression gate prolazi

## 13. B11 odluka

B11 preporuka:

Ne implementirati endpoint dok ne postoji odobrena migracija, permission model, audit event naming update i regression test plan.

Sljedeci sigurni korak:

`Program 1 Phase B12 - Snapshot Permission and Audit Contract`
