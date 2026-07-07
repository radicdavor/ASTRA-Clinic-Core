# Program 1 Phase B2 - Clinical Readiness API Contract

Status: documentation-only API contract

## 1. Svrha

Ovaj dokument definira buduci API contract za read-only Clinical Readiness Preview.

Ovaj dokument je:

- documentation-only
- bez implementiranog endpointa
- bez koda
- bez DB modela
- bez UI-ja
- bez produkcijskog odobrenja
- bez real-data odobrenja
- bez certified EMR claim
- bez medical-device claim

Svrha je omoguciti sigurnu buducu implementaciju previewa bez mijesanja s Operational Readiness i bez stvaranja klinicke odluke.

## 2. API principle

Prvi buduci API mora biti read-only.

Ne smije:

- blokirati termine
- mijenjati appointment status
- kreirati taskove
- kreirati ClinicalPlan
- kreirati Episode
- kreirati Outcome Evidence
- slati poruke
- overrideati readiness
- oznaciti pacijenta kao ready
- koristiti unreviewed AI output kao source

API smije samo izracunati i vratiti preview temeljen na dopustenim izvorima.

## 3. Proposed future endpoint

Predlozeni buduci endpoint:

`GET /api/appointments/{appointment_id}/clinical-readiness-preview`

Ovaj endpoint nije implementiran u B2.

Appointment-scoped pristup je preporucen zato sto:

- Clinical Readiness je patient/service/procedure-specific
- Appointment povezuje patient, service, provider, room i vrijeme
- izbjegava zahtjev da postoji Clinical Episode
- prirodno pripada buducem Appointment Workspace previewu

Endpoint ne smije koristiti `/api/readiness`, jer je to Operational Readiness.

## 4. Response shape

Konceptualni JSON response:

```json
{
  "appointment_id": 1,
  "patient_id": 1,
  "service_id": 1,
  "status": "ready_with_warning",
  "is_preview": true,
  "generated_at": "2026-07-07T12:00:00Z",
  "summary": "Klinicka spremnost je prikazana kao read-only preview.",
  "items": [
    {
      "key": "sedation_escort",
      "label": "Pratnja nakon sedacije",
      "category": "sedation_anesthesia",
      "status": "needs_nurse_action",
      "severity": "warning",
      "responsible_role": "nurse",
      "source_type": "human_attestation",
      "source_ref": null,
      "source_label": null,
      "suggested_action": "Provjeriti ima li pacijent pratnju.",
      "blocking": false,
      "override_allowed": true,
      "override_role": "physician",
      "override_reason_required": true,
      "audit_required": false
    }
  ],
  "source_warnings": [],
  "limitations": []
}
```

Polja moraju mapirati B1 vocabulary, taxonomy i source/evidence mapping.

## 5. Response fields

Top-level fields:

- `appointment_id`: ID termina za koji je preview generiran.
- `patient_id`: ID pacijenta povezanog s terminom.
- `service_id`: ID usluge/procedure/tretmana povezanog s terminom.
- `status`: agregirani `Clinical Readiness Status`.
- `is_preview`: uvijek `true` u prvoj implementaciji.
- `generated_at`: vrijeme generiranja previewa.
- `summary`: kratko objasnjenje da je prikaz read-only preview.
- `items`: lista `Clinical Readiness Item` stavki.
- `source_warnings`: upozorenja o ogranicenjima izvora.
- `limitations`: poznata ogranicenja previewa.

Item fields:

- `key`: stabilni kljuc itema.
- `label`: korisnicka labela.
- `category`: `Clinical Readiness Category`.
- `status`: status itema.
- `severity`: `Clinical Readiness Severity`.
- `responsible_role`: uloga koja moze pregledati ili rijesiti item.
- `source_type`: evidence level/source type.
- `source_ref`: referenca na source object ako postoji.
- `source_label`: kratka labela izvora za source badge.
- `suggested_action`: sigurna preporuka sto pregledati ili uciniti.
- `blocking`: oznacava je li item blokirajuci u buducem governance modelu.
- `override_allowed`: smije li se item u buducnosti overrideati.
- `override_role`: uloga koja bi smjela overrideati.
- `override_reason_required`: treba li razlog.
- `audit_required`: treba li audit kada se item potvrdi/overridea u buducnosti.

## 6. Error states

Buduci error/limitation slucajevi:

- appointment not found
- appointment missing patient/service
- patient has no reviewed clinical knowledge
- service has no readiness template
- unsupported service
- insufficient permission

Nedostatak templatea ili reviewed sources ne mora uvijek biti hard error. U read-only previewu moze biti `limitations` entry ako je appointment inace valjan.

## 7. Permissions

Vjerojatne buduce dozvole:

- read-only preview: `clinical_readiness.read`
- future override: `clinical_readiness.override`
- future configure templates: `clinical_readiness.configure`

Dozvole se ne implementiraju u B2.

## 8. Relationship to `/api/readiness`

`/api/readiness` ostaje Operational Readiness.

Clinical Readiness Preview ne smije ponovno koristiti `/api/readiness`.

U API dokumentaciji rijec `readiness` mora uvijek biti kvalificirana:

- `operational_readiness`
- `clinical_readiness`

Nijedan buduci endpoint ne smije implicirati da Operational Readiness predstavlja klinicku spremnost pacijenta za postupak.

