# Program 1 Phase B12 - Snapshot Permission / Audit No-Go Matrix

Status: documentation-only no-go matrix

## 1. Svrha

Ova matrica definira sigurnosne odluke za buduci Clinical Readiness Snapshot capture.

Ovaj dokument ne implementira permissione, audit evente, endpoint, UI, DB tablicu ili migraciju.

Matrica postoji kako buduca implementacija ne bi slucajno pretvorila snapshot u:

- clinical approval
- readiness override
- task
- Outcome Evidence
- appointment status change
- AI decision

## 2. No-Go matrix

| Scenario | Allowed? | Required permission | Required audit? | Required reason? | Why / Notes |
| --- | --- | --- | --- | --- | --- |
| Physician captures snapshot. | Da, buduce. | `clinical_readiness.snapshots.write` | Da, `clinical_readiness_snapshot_captured`. | Da. | Dopusteno samo kao explicit preview snapshot, ne clinical approval. |
| Nurse captures operational snapshot. | Uvjetno / deferred. | `clinical_readiness.snapshots.write` ako governance posebno dopusti. | Da. | Da. | Samo operational preview context; default nije dopusteno za physician-only clinical snapshot. |
| Reception captures clinical snapshot. | Ne default. | N/A | N/A | N/A | Reception radi operativni tijek, ne clinical readiness capture. |
| AI agent captures snapshot. | Ne. | N/A | N/A | N/A | AI ne smije captureati, supersedeati ili finalizirati snapshot. |
| API key captures snapshot. | Ne default. | Future explicit write scope samo uz maintainer odluku. | Da ako ikad odobreno. | Da, human-supplied. | Integracija ne smije zaobici ljudski razlog i audit. |
| System auto-captures on page load. | Ne. | N/A | N/A | N/A | Preview read ne smije stvoriti snapshot. |
| User views snapshot history. | Da, buduce. | `clinical_readiness.snapshots.read` | Ne default; view audit samo ako governance zatrazi. | Ne. | History view je read-only. |
| User supersedes snapshot. | Da, buduce i ograniceno. | `clinical_readiness.snapshots.supersede` | Da, `clinical_readiness_snapshot_superseded`. | Da. | Stari snapshot ostaje immutable; supersede stvara history interpretaciju. |
| User deletes snapshot. | Ne. | N/A | N/A | N/A | Snapshot je immutable audit-relevant record. |
| User edits snapshot payload. | Ne. | N/A | N/A | N/A | Payload je copied preview u trenutku capturea i ne smije se mijenjati. |
| User captures snapshot without reason. | Ne. | `clinical_readiness.snapshots.write` nije dovoljno. | Ne smije doci do capturea. | Da, obavezno. | Prazan reason je No-Go. |
| User captures snapshot and changes appointment status. | Ne. | N/A | N/A | N/A | Capture ne smije mijenjati appointment workflow. |
| User captures snapshot and creates Task. | Ne. | N/A | N/A | N/A | Task engine nije dio snapshot capturea. |
| User captures snapshot and creates Outcome Evidence. | Ne. | N/A | N/A | N/A | Snapshot nije dokaz ishoda. |
| User captures snapshot and sends patient message. | Ne. | N/A | N/A | N/A | Snapshot history nije patient communication workflow. |
| User captures snapshot from unreviewed AI. | Ne ako se unreviewed AI koristi kao official source. | N/A | N/A | N/A | AI prijedlog bez reviewa ne smije postati official knowledge. |
| User captures snapshot where Patient Clinical Summary is only source. | Ne ako summary sluzi kao source of truth. | N/A | N/A | N/A | Summary je view, ne izvor istine. Snapshot mora koristiti reviewed source-linked evidence. |
| User captures snapshot with limitations visible. | Da, buduce. | `clinical_readiness.snapshots.write` | Da. | Da. | Limitations moraju ostati vidljive u snapshotu i UI-ju. |
| User captures snapshot with open questions visible. | Da, buduce. | `clinical_readiness.snapshots.write` | Da. | Da. | Open questions ostaju warningi, ne taskovi. |
| User captures snapshot after template version changed. | Da, buduce. | `clinical_readiness.snapshots.write` | Da. | Da. | Snapshot mora spremiti template version koja je vrijedila u trenutku capturea. |

## 3. Hard No-Go pravila

Buduca implementacija ne smije:

- captureati snapshot bez eksplicitnog user actiona
- captureati snapshot bez reasona
- dopustiti AI agentu capture
- dopustiti system job auto-capture
- editirati snapshot payload
- brisati snapshot
- koristiti Patient Clinical Summary kao source of truth
- koristiti unreviewed AI kao official source
- sakriti limitations
- pretvoriti open questions u taskove bez zasebnog human-confirmed task workflowa
- promijeniti appointment status
- stvoriti Outcome Evidence
- stvoriti ClinicalPlan ili Episode
- prikazati snapshot kao clinical approval

## 4. Conditional-Go pravila

Sljedece smije biti razmotreno kasnije samo uz zaseban maintainer decision:

- nurse operational capture
- API key capture scope
- view audit event
- supersession UI
- warning za template version drift

Svaki conditional-go mora imati:

- permission
- reason
- audit
- regression test
- UI disclaimer

## 5. B12 matrix odluka

Default mora biti deny.

Capture je dopusten samo kada je:

- korisnik autoriziran
- reason prisutan
- server-side preview rebuild uspjesan
- immutable payload spremljen
- audit event spremljen u istoj transakciji
- snapshot jasno oznacen kao preview-only

Sljedeci dokument u B12 passu definira implementation gate prije bilo kakve migracije ili endpointa.
