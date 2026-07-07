# Program 1 Phase B9 - Clinical Readiness Snapshot Persistence Model

Status: design-only, no implementation

## 1. Svrha

B9 definira buduci persistence model za Clinical Readiness Snapshot.

Ovaj dokument je samo dizajn. Ne uvodi:

- DB tablicu sada
- Alembic migraciju sada
- capture endpoint sada
- snapshot history UI sada
- Outcome Evidence
- klinicku odluku
- workflow enforcement

Cilj je unaprijed definirati sto bi buduci trajni snapshot morao spremiti, kako bi se izbjeglo da persistence nenamjerno postane clinical approval, readiness clearance, task state ili audit replacement.

## 2. Future table concept

Buduca konceptualna tablica:

`clinical_readiness_snapshots`

Konceptualna polja:

- `id`
- `appointment_id`
- `patient_id`
- `service_id`
- `created_at`
- `created_by_user_id`
- `schema_version`
- `preview_generated_at`
- `preview_status`
- `preview_summary`
- `template_key`
- `template_label`
- `template_version`
- `template_binding_status`
- `template_binding_warning`
- `snapshot_reason`
- `is_preview_snapshot`
- `items_json`
- `limitations_json`
- `source_warnings_json`
- `source_refs_json`
- `disclaimer`
- `superseded_by_snapshot_id`
- `superseded_at`
- `superseded_reason`

Ova tablica se ne implementira u B9.

Ako se kasnije odobri migracija, table shape mora ponovno proci review prije pisanja Alembic migracije.

## 3. Immutable JSON payloads

Snapshot mora spremiti ono sto je preview prikazao, a ne recomputeati prikaz kasnije.

Posebno se u snapshot payload kopiraju:

- readiness items
- limitations
- source warnings
- source references
- preview summary
- template metadata
- binding metadata
- preview-only disclaimer

Razlog:

- templatei se mogu promijeniti
- reviewed documents se mogu promijeniti
- Open Questions se mogu promijeniti
- service binding se moze promijeniti
- template version se moze povuci ili zamijeniti

Ako snapshot kasnije recomputea sadrzaj, vise ne predstavlja ono sto je korisnik tada vidio.

## 4. Source references

Buduci snapshot treba zabiljeziti source references, a ne duplicirati izvorne klinicke dokumente.

Dopustene reference:

- reviewed ClinicalDocument ids
- Patient Clinical Knowledge item source refs
- appointment id
- service id
- template key/version
- human attestation refs kada buduci model postoji

Zabranjeno kao official source:

- unreviewed AI
- draft ClinicalDocument
- rejected ClinicalDocument
- superseded ClinicalDocument
- Patient Clinical Summary kao source truth
- free text bez source referencea

Snapshot moze reci da je preview prikazao limitation ili warning zbog nedostatka izvora. To ne znaci da nedostajuci ili nepregledani izvor postaje sluzbeni dokaz.

## 5. What persistence does not mean

Persistent snapshot nije:

- clinical approval
- procedure allowed decision
- physician confirmation
- Outcome Evidence
- Task completion
- readiness clearance
- consent
- medical note
- patient instruction

Persistence znaci samo:

`ASTRA je spremila sto je Clinical Readiness Preview prikazao u tom trenutku.`

Lijecnik i dalje odlucuje. Snapshot ne odlucuje.
