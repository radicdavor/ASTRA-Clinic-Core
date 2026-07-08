# Program 1 Phase D114 - Open Question Read Error State Contract

Status: documented

## Error States

| State | Future response expectation | Safe user-facing wording | Side effects |
| --- | --- | --- | --- |
| Unauthenticated | 401 | Prijava je potrebna za prikaz source-linked pitanja. | none |
| Permission denied | 403 | Nemate dozvolu za prikaz open question zapisa. | none |
| Unknown patient | 404 | Pacijent nije pronaden. | none |
| Unknown question | 404 | Open question zapis nije pronaden. | none |
| Out-of-scope question | 404 or 403 | Open question zapis nije dostupan u ovom opsegu. | none |
| Invalid finding scope | 404 or 422 | Finding scope nije valjan za ovog pacijenta. | none |
| Empty result | 200 empty list | Nema prikazanih source-linked pitanja za ovaj opseg. | none |
| Backend unavailable | 503 or network error | Open question zapisi trenutno nisu dostupni. | none |
| Malformed id | 422 | Identifikator nije valjan. | none |

## Forbidden Error Text

- diagnosis failed
- treatment blocked
- clearance denied
- approval denied
- patient unsafe
- issue resolved

## Clinical Boundary

Read API errors must not imply clinical decision, patient readiness, treatment status, diagnosis, approval, clearance or resolution.
