# Program 1 Phase D75 - Extraction Contract Go/No-Go Matrix

Status: go/no-go matrix

| Surface | Status | Demo/Pilot | Real Data | Production | Decision |
| --- | --- | --- | --- | --- | --- |
| ClinicalDocument extraction contract | Complete | Go | No-go | No-go | Allowed |
| Candidate boundary | Complete | Go | No-go | No-go | Allowed |
| Source traceability | Complete | Go | No-go | No-go | Required |
| Confidence/limitations | Complete | Go | No-go | No-go | Required |
| Human review gate | Complete | Go | No-go | No-go | Required |
| Passive schema | Added | Go with tests | No-go | No-go | Allowed as passive shape |
| Safety tests | Added | Go | No-go | No-go | Required |
| CI gate | Documented | Go | No-go | No-go | Maintain |
| Extraction endpoint | Not implemented | No-go | No-go | No-go | Forbidden |
| OCR runtime | Not implemented | No-go | No-go | No-go | Forbidden |
| AI runtime | Not implemented | No-go | No-go | No-go | Forbidden |
| Automatic persistence | Not implemented | No-go | No-go | No-go | Forbidden |
| Review endpoint | Not implemented | No-go | No-go | No-go | Deferred |
| Task engine | Not implemented | No-go | No-go | No-go | Forbidden |
| Outcome Evidence | Not implemented | No-go | No-go | No-go | Forbidden |
| Patient messaging | Not implemented | No-go | No-go | No-go | Forbidden |
| Automatic diagnosis/treatment | Not implemented | No-go | No-go | No-go | Forbidden |
| Production | Not approved | No-go | No-go | No-go | Blocked |
| Real data | Not approved | No-go | No-go | No-go | Blocked |

## Conclusion

Documentation and passive schema are allowed.

Runtime extraction, automatic persistence, production and real-data use remain no-go.

