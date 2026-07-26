# PR #3 fifth security rescan — clinical-document response surface

Scanned revision: `f89ac29475cb2cb26d25d7d44fd3a2c5fa2405f4`

The sealed scan identified one shared response-projection defect. Parent
`ClinicalDocument` authorization remains institution scoped; the broad nested
`PatientOut` widened the response after authorization.

| Route | Producer | Parent scoping | Patient fields before remediation | Notes exposure | Required replacement |
| --- | --- | --- | --- | --- | --- |
| `GET /api/clinical-documents` | `ClinicalDocumentOut[]` | Institution clinical read | Broad `PatientOut` | Yes | Exact document identity DTO |
| `GET /api/clinical-documents/search` | `ClinicalDocumentOut[]` | Institution clinical read | Broad `PatientOut` | Yes | Exact document identity DTO |
| `GET /api/clinical-documents/{id}` | `ClinicalDocumentOut` | Institution clinical read | Broad `PatientOut` | Yes | Exact document identity DTO |
| `GET /api/patients/{id}/clinical-documents` | `ClinicalDocumentOut[]` | Institution clinical read plus patient filter | Broad `PatientOut` | Yes | Exact document identity DTO |
| `POST /api/clinical-documents` | `ClinicalDocumentOut` | Medical write plus canonical provenance | Broad `PatientOut` | Yes, same schema family | Inherit exact document identity DTO |
| `POST /api/patients/{id}/clinical-documents` | `ClinicalDocumentOut` | Medical write plus route-patient match | Broad `PatientOut` | Yes, same schema family | Inherit exact document identity DTO |
| `POST /api/clinical-documents/upload` | `ClinicalDocumentOut` | Medical write plus canonical provenance | Broad `PatientOut` | Yes, same schema family | Inherit exact document identity DTO |
| `PATCH /api/clinical-documents/{id}` | `ClinicalDocumentOut` | Author-owned editable draft | Broad `PatientOut` | Yes, same schema family | Inherit exact document identity DTO |
| `POST /api/clinical-documents/{id}/extract` | `ClinicalDocumentOut` | Institution read plus review permission | Broad `PatientOut` | Yes, same schema family | Inherit exact document identity DTO |
| `POST /api/clinical-documents/{id}/review` | `ClinicalDocumentOut` | Institution read plus clinical write | Broad `PatientOut` | Yes, same schema family | Inherit exact document identity DTO |
| `POST /api/clinical-documents/{id}/reject-summary` | `ClinicalDocumentOut` | Institution read plus clinical write | Broad `PatientOut` | Yes, same schema family | Inherit exact document identity DTO |

Classification review, source download, evidence timeline, addenda, readiness
and signed-report endpoints do not produce `ClinicalDocumentOut.patient`; they
remain governed by their existing response types and authorization controls.

The approved embedded identity allowlist is:

- `id`
- `first_name`
- `last_name`
- `date_of_birth`

Contact data, OIB, timestamps, audit metadata and all free-text fields are
detail-only data outside the clinical-document response contract.
