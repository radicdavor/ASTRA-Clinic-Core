# Program 1 Phase B0 - Clinical Readiness Specialty Examples

Status: documentation-only examples

## Svrha

Ovaj dokument daje primjere kako bi Clinical Readiness Gate mogao izgledati po specijalnostima.

Primjeri nisu klinicke smjernice, nisu produkcijska pravila i ne odobravaju automatsku odluku sustava. Sluzit ce kao materijal za buduci vocabulary i domain mapping.

# Gastroenterology examples

## Gastroscopy readiness

Primjeri readiness itema:

| Item | Classification |
| --- | --- |
| Fasting status deklariran | nurse-check, warning, override-possible |
| Anticoagulants/antiaggregants provjereni | physician-review, warning, override-possible |
| Alergije poznate ili provjerene | nurse-check, physician-review if positive, warning |
| Sedation escort prisutan ako je sedacija planirana | admin-check, blocking, override-possible only by physician/governance |
| Consent prisutan | admin-check, nurse-check, document-required, blocking |
| Prethodni relevantni nalazi pregledani ako postoje | physician-review, document-required, warning |
| Alarm symptoms zabiljezeni | physician-review, warning |
| Otvorena PHD/lab/radiology pitanja | physician-review, warning or blocking |
| Potreba za bolnickim settingom kod visokog rizika | physician-review, blocking |

Napomena:

Gastroscopy readiness ne smije automatski odluciti da je postupak siguran. Moze prikazati sto nedostaje i sto zahtijeva review.

## Colonoscopy readiness

Primjeri readiness itema:

| Item | Classification |
| --- | --- |
| Bowel prep declared | nurse-check, warning, override-possible |
| Anticoagulants/antiaggregants provjereni | physician-review, warning or blocking |
| Diabetes medications ako relevantno | physician-review, warning |
| Sedation escort prisutan ako je sedacija planirana | admin-check, blocking |
| Consent za colonoscopy/sedation/polypectomy | document-required, blocking |
| Prethodna colonoscopy/PHD dostupna ako je relevantna | document-required, physician-review, warning |
| Family history zabiljezena ako je relevantna | physician-review, warning |
| High-risk comorbidities | physician-review, blocking if severe |
| Material readiness: snares/clips gdje relevantno | nurse-check, inventory/material prerequisite, warning or blocking |

Napomena:

Material readiness je operativni/inventory signal. Klinicki rizik ostaje lijecnicka odluka.

## H. pylori treatment/test-of-cure readiness

Primjeri readiness itema:

| Item | Classification |
| --- | --- |
| Prior therapy known | physician-review, document-required, warning |
| Allergy to penicillin | physician-review, warning or blocking |
| PPI/antibiotic/bismuth timing poznat | physician-review, warning |
| Test-of-cure timing odgovara planu | physician-review, warning |
| Pregnancy if relevant | physician-review, blocking if applicable |
| Previous resistance/failure if known | physician-review, document-required, warning |

Napomena:

Ovaj readiness primjer ne propisuje terapiju. Samo strukturira sto treba biti poznato prije odluke.

# Aesthetic medicine examples

## Injectable treatment readiness

Primjeri readiness itema:

| Item | Classification |
| --- | --- |
| Pregnancy/breastfeeding status | physician-review, blocking or warning |
| Active infection/herpes | physician-review, blocking |
| Anticoagulants | physician-review, warning |
| Known allergies | nurse-check, physician-review if positive, warning |
| Prior filler type/material | physician-review, document-required if available, warning |
| Prior complications | physician-review, warning or blocking |
| Unrealistic expectations | physician-review, blocking or warning |
| Consent | document-required, blocking |
| Baseline photographs | admin-check, document-required, warning |
| Product/batch availability | inventory/material prerequisite, nurse-check, blocking if unavailable |

Napomena:

Ocekivanja pacijenta i indikacija nisu administrativna provjera. To je physician-review.

## Polynucleotide/skinbooster readiness

Primjeri readiness itema:

| Item | Classification |
| --- | --- |
| Active infection | physician-review, blocking |
| Autoimmune/inflammatory concerns where relevant | physician-review, warning |
| Prior reaction | physician-review, warning or blocking |
| Product availability | inventory/material prerequisite, nurse-check, blocking if unavailable |
| Treatment interval | physician-review, warning |
| Consent | document-required, blocking |
| Photo documentation | admin-check, document-required, warning |

Napomena:

Sustav smije podsjetiti na interval i dokumentaciju, ali ne smije sam odluciti o indikaciji.

## Energy-based treatment readiness

Primjeri readiness itema:

| Item | Classification |
| --- | --- |
| Contraindicated device/implant/pacemaker if relevant | physician-review, blocking |
| Skin condition in treatment area | physician-review, warning or blocking |
| Recent procedures | physician-review, warning |
| Consent | document-required, blocking |
| Treatment area documentation | admin-check, document-required, warning |

Napomena:

Energy-based readiness mora biti vezan uz konkretan uredaj i tretman u buducem modelu, ali B0 ne uvodi procedure/treatment template engine.

## Cross-specialty rule

Ako readiness item moze imati klinicku posljedicu, default odgovornost je physician-review.

Ako readiness item samo potvrduje prisutnost dokumenta, termina, resursa ili identiteta, moze biti admin-check ili nurse-check ako je to eksplicitno definirano.

