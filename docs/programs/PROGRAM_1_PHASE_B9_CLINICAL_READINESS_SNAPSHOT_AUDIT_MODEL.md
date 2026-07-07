# Program 1 Phase B9 - Clinical Readiness Snapshot Audit Model

Status: design-only, no implementation

## 1. Svrha

Ovaj dokument definira buducu audit semantiku za Clinical Readiness Snapshot capture.

B9 ne dodaje audit evente u kod. Ovdje se samo definira kako bi buduci audit trebao izgledati ako se snapshot persistence posebno odobri.

## 2. Audit event names

Predlozeni buduci audit event names:

- `clinical_readiness_snapshot_captured`
- `clinical_readiness_snapshot_viewed`
- `clinical_readiness_snapshot_superseded`

Ovo su future names only.

Nisu implementirani sada.

Ako se u buducnosti uvedu, moraju biti dokumentirani u Program 1 audit naming dokumentu i pokriveni regression testovima.

## 3. Audit payload

Buduci capture audit payload treba ukljuciti:

- snapshot id
- appointment id
- patient id
- service id
- template key
- template version
- captured by
- capture reason
- preview status
- item count
- limitation count

Audit payload ne treba duplicirati cijeli snapshot JSON ako sam snapshot vec cuva immutable content.

Audit treba biti citljiv trag akcije, dok snapshot cuva sadrzaj prikaza.

## 4. What audit must prove

Audit mora dokazati:

- tko je captureao snapshot
- kada je snapshot capturean
- iz kojeg appointmenta je nastao
- koji template key/version je koristen
- je li snapshot bio preview-only
- jesu li postojala ogranicenja

Minimalno pitanje koje audit mora odgovoriti:

`Tko je namjerno spremio ovaj preview prikaz i zasto?`

## 5. What audit must not imply

Audit ne smije implicirati:

- pacijent je klinicki spreman
- postupak je odobren
- lijecnik je prihvatio sva upozorenja
- readiness je overridean
- task je dovrsen
- outcome se dogodio

Audit event za capture smije znaciti samo:

`Snapshot previewa je zabiljezen.`

## 6. Relation to existing AuditLog

Buduci snapshot capture pise normalan `AuditLog` event.

Snapshot ne zamjenjuje `AuditLog`.

`AuditLog` ne zamjenjuje snapshot content.

Odnos je:

- `AuditLog` biljezi akciju capturea, viewa ili supersessiona.
- Snapshot cuva immutable kopiju preview sadrzaja.

Ako snapshot capture ne moze napisati audit, persistence se ne smije smatrati prihvatljivom za buducu fazu.
