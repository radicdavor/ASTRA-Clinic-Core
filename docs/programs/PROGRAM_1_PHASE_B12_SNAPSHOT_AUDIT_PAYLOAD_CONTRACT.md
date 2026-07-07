# Program 1 Phase B12 - Snapshot Audit Payload Contract

Status: documentation-only audit contract

## 1. Svrha

Ovaj dokument definira buducu audit semantiku i payload oblik za Clinical Readiness Snapshot.

Ovaj dokument ne implementira audit evente u kodu.

Ovaj dokument ne dodaje:

- backend rutu
- frontend UI
- DB migraciju
- snapshot persistence
- audit write logiku
- permission enforcement
- Outcome Evidence
- Task engine
- override
- appointment status change

Audit mora zapisati da je korisnik spremio snapshot preview prikaza.

Audit ne smije implicirati da je pacijent klinicki odobren, da je postupak dopusten ili da je lijecnik prihvatio sve warninge.

## 2. Buduci audit eventi

Svi event names u ovom dokumentu su future-only i nisu implementirani u B12.

| Event name | Kada nastaje | Znaci | Ne znaci |
| --- | --- | --- | --- |
| `clinical_readiness_snapshot_captured` | Kada ovlasteni korisnik eksplicitno capturea snapshot uz razlog. | Immutable preview copy je spremljen i auditiran. | Clinical approval, override, task, outcome ili appointment status change. |
| `clinical_readiness_snapshot_viewed` | Samo ako buduci governance odluci auditirati view. | Korisnik je otvorio snapshot. | Da je korisnik prihvatio sadrzaj snapshota. |
| `clinical_readiness_snapshot_superseded` | Kada noviji snapshot zamijeni stariji u history interpretaciji. | Stari snapshot ostaje sacuvan, ali je oznacen kao superseded. | Da je stari payload editiran ili obrisan. |

## 3. Capture audit payload

Buduci `clinical_readiness_snapshot_captured` audit payload mora minimalno sadrzavati:

```json
{
  "snapshot_id": 123,
  "appointment_id": 456,
  "patient_id": 789,
  "service_id": 10,
  "created_by_user_id": 5,
  "capture_reason": "Pilot review prije kolonoskopije.",
  "schema_version": "clinical-readiness-snapshot-v1",
  "preview_generated_at": "2026-07-07T10:31:00Z",
  "preview_status": "ready_with_warning",
  "template_key": "colonoscopy",
  "template_label": "Kolonoskopija",
  "template_version": "demo-v1",
  "template_binding_status": "explicit",
  "item_count": 8,
  "blocking_item_count": 0,
  "limitation_count": 2,
  "source_warning_count": 1,
  "is_preview_snapshot": true,
  "disclaimer": "Snapshot je zapis preview prikaza, ne clinical approval."
}
```

Required fields:

- `snapshot_id`
- `appointment_id`
- `patient_id`
- `service_id`
- `created_by_user_id`
- `capture_reason`
- `schema_version`
- `preview_generated_at`
- `preview_status`
- `template_key`
- `template_label`
- `template_version`
- `template_binding_status`
- `item_count`
- `blocking_item_count`
- `limitation_count`
- `source_warning_count`
- `is_preview_snapshot`
- `disclaimer`

Payload smije imati dodatne diagnostic/debug metapodatke samo ako ne sadrze nepotrebne osjetljive klinicke detalje i ako su pokriveni testovima.

## 4. Supersede audit payload

Buduci `clinical_readiness_snapshot_superseded` audit payload mora minimalno sadrzavati:

```json
{
  "old_snapshot_id": 123,
  "new_snapshot_id": 124,
  "appointment_id": 456,
  "patient_id": 789,
  "superseded_by_user_id": 5,
  "supersede_reason": "Novi snapshot nakon pregleda vanjskog nalaza.",
  "old_template_version": "demo-v1",
  "new_template_version": "demo-v2",
  "old_preview_status": "ready_with_warning",
  "new_preview_status": "not_ready"
}
```

Supersede ne smije:

- editirati payload starog snapshota
- brisati stari snapshot
- sakriti stari snapshot iz audit traila
- stvarati Outcome Evidence
- mijenjati appointment status
- znaciti clinical approval

## 5. View audit payload

Postoje dvije opcije za buduci `clinical_readiness_snapshot_viewed` event:

Option A:

- ne auditirati svaki view
- smanjiti audit noise
- osloniti se na capture/supersede audit

Option B:

- auditirati view samo kada snapshot sadrzi osjetljiv ili visokorizican clinical warning
- koristiti minimalni payload

Preporuka:

Poceti bez view audit eventa osim ako compliance/governance kasnije izricito zatrazi suprotno.

Ako se view audit uvede, payload treba biti minimalan:

```json
{
  "snapshot_id": 123,
  "appointment_id": 456,
  "patient_id": 789,
  "viewed_by_user_id": 5,
  "view_context": "appointment_workspace_history"
}
```

View audit ne znaci da je korisnik prihvatio ili potvrdio clinical readiness.

## 6. Audit event ne smije implicirati

Nijedan snapshot audit event ne smije znaciti:

- pacijent je clinical ready
- postupak je odobren
- lijecnik je prihvatio sve warninge
- readiness je overridean
- task je zavrsen
- Outcome Evidence je nastao
- pacijent je obavijesten
- AI je donio odluku
- Patient Clinical Summary je source of truth

UI i docs moraju zadrzati disclaimer:

`Snapshot je zapis preview prikaza, ne clinical approval.`

## 7. Transaction boundary

Buduca capture transakcija mora biti atomicna:

1. validacija korisnika i permissiona
2. validacija razloga
3. server-side rebuild previewa
4. spremanje immutable snapshota
5. zapis audit eventa
6. commit

Pravila:

- ako audit write ne uspije, capture mora failati
- ako snapshot save ne uspije, audit event ne smije ostati
- capture ne smije u istoj transakciji mijenjati appointment status
- capture ne smije stvarati Task, Outcome Evidence, ClinicalPlan ili Episode
- capture ne smije oznaciti readiness kao cleared/approved

## 8. Audit payload safety

Audit payload treba biti dovoljno bogat za rekonstrukciju akcije, ali ne smije nepotrebno duplicirati cijeli snapshot payload ako to nije potrebno.

Snapshot payload ostaje u snapshot tablici.

Audit payload treba sadrzavati:

- identifikatore
- actor
- reason
- status/template metadata
- counts
- disclaimer

Audit payload ne treba sadrzavati cijeli clinical text osim ako maintainer kasnije izricito ne odluci drugacije.

## 9. B12 audit odluka

Buduca implementacija mora uvesti audit event tek zajedno sa snapshot persistenceom i capture endpointom.

Nije dopusteno implementirati capture bez audit eventa.

Nije dopusteno implementirati audit event koji zvuci kao clinical approval.

Sljedeci dokument u B12 passu definira no-go matrix za permission i audit situacije.
