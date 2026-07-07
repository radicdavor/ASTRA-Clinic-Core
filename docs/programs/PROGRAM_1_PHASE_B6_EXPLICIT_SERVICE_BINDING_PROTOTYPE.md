# Program 1 Phase B6 - Clinical Readiness Explicit Service Binding Prototype

Status: demo/pilot-only prototype

## 1. Svrha

B6 uvodi prvi sigurni prototip eksplicitnog vezanja Clinical Readiness templatea na katalog usluga bez database migracije.

Ovaj prototip je:

- demo/pilot-only
- read-only
- non-blocking
- konfiguracijski, ne produkcijski
- bez DB binding fielda
- bez template editora
- bez enforcementa
- bez override workflowa
- bez Task enginea
- bez real AI/OCR
- bez real patient data odobrenja

Svrha je dokazati redoslijed odabira templatea:

1. eksplicitni demo binding
2. keyword fallback
3. generic fallback

## 2. Zasto explicit binding prototype

B4 keyword matching je koristan, ali krhak.

B5 je definirao da buduci explicit binding treba imati prednost pred keyword fallbackom.

B6 pokazuje taj smjer bez dodavanja DB polja:

- service code moze stabilnije predstavljati uslugu od naziva
- explicit demo config je citljiv u kodu
- preview moze jasno prikazati da je binding eksplicitan, ali jos demo/pilot
- promjena ne uvodi admin editor ni produkcijska pravila

## 3. Prototype scope

B6 smije:

- dodati staticni demo binding config
- preferirati explicit binding prije keyword fallbacka
- prikazati `template_binding_status="explicit"`
- prikazati warning da je binding demo/pilot konfiguracija
- pokriti ponasanje testovima

B6 ne smije:

- dodati `clinical_readiness_template_key` u `services` tablicu
- dodati Alembic migraciju
- dodati UI za binding
- auditirati read-only preview
- mijenjati appointment status
- kreirati task, episode, ClinicalPlan ili Outcome Evidence
- tvrditi produkcijsku spremnost

## 4. Demo binding strategy

Prvi prototip koristi staticnu konfiguraciju u backend service sloju.

Preferirani kljuc:

- `Service.code`

Fallback za demo:

- tocno normalizirano ime usluge

Primjeri demo bindinga:

| Service code/name | Template |
| --- | --- |
| `GASTROSCOPY`, `GASTRO` | `gastroscopy` |
| `COLONOSCOPY`, `COLO` | `colonoscopy` |
| `HPYLORI` | `hpylori` |
| `FILLER`, `BOTOX` | `aesthetic_injectable` |
| `SKINBOOSTER`, `PN` | `aesthetic_skinbooster_pn` |
| `LASER`, `RF`, `EXION` | `aesthetic_energy_device` |

Ovi bindingi su demo konfiguracija, nisu produkcijski service catalog governance.

## 5. Binding precedence

B6 runtime precedence:

1. explicit demo service binding
2. service-name keyword fallback
3. generic fallback

Ako explicit binding postoji, keyword fallback se ne koristi.

To je vazno jer usluga moze imati naziv koji sadrzi krivi keyword, ali stabilan code koji pokazuje pravi demo template.

## 6. UI/API transparency

Preview response treba jasno prikazati:

- `template_key`
- `template_label`
- `template_binding_status`
- `template_binding_warning`

Za explicit demo binding:

- `template_binding_status="explicit"`
- warning mora reci da je rijec o demo/pilot explicit binding konfiguraciji, ne produkcijskom pravilu

UI ne smije dodati:

- `Bind template`
- `Edit template`
- `Mark ready`
- `Override`
- `Create task`
- `AI cleared`

## 7. Safety

Explicit binding u B6 ne znaci clinical clearance.

Template item je i dalje samo prompt/check.

Preview ostaje:

- read-only
- appointment-scoped
- non-blocking
- odvojen od Operational Readinessa
- bez real AI/OCR
- bez stvarnih podataka

Ako binding governance nije jasan, default ostaje warning i ljudski pregled.
