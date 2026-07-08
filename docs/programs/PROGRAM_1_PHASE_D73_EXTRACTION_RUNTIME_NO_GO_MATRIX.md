# Program 1 Phase D73 - Extraction Runtime No-Go Matrix

Status: runtime no-go matrix

| Surface | Status | Demo/Pilot | Real Data | Production | Decision |
| --- | --- | --- | --- | --- | --- |
| Extraction contract | Documented | Go | No-go | No-go | Allowed |
| Candidate boundary | Documented | Go | No-go | No-go | Allowed |
| Source traceability | Documented | Go | No-go | No-go | Required |
| Confidence/limitations | Documented | Go | No-go | No-go | Required |
| Human review gate | Documented | Go | No-go | No-go | Required |
| Passive schema | Added | Go with tests | No-go | No-go | Allowed as non-runtime shape |
| Safety regression | Added | Go | No-go | No-go | Required |
| OCR runtime | Not implemented | No-go | No-go | No-go | Forbidden |
| AI provider runtime | Not implemented | No-go | No-go | No-go | Forbidden |
| Extraction endpoint | Not implemented | No-go | No-go | No-go | Forbidden |
| Background job | Not implemented | No-go | No-go | No-go | Forbidden |
| Automatic finding creation | Not implemented | No-go | No-go | No-go | Forbidden |
| Finding persistence from candidate | Not implemented | No-go | No-go | No-go | Deferred |
| Review endpoint | Not implemented | No-go | No-go | No-go | Deferred |
| Task engine | Not implemented | No-go | No-go | No-go | Forbidden |
| Outcome Evidence | Not implemented | No-go | No-go | No-go | Forbidden |
| Patient messaging | Not implemented | No-go | No-go | No-go | Forbidden |
| Automatic diagnosis | Not implemented | No-go | No-go | No-go | Forbidden |
| Automatic treatment | Not implemented | No-go | No-go | No-go | Forbidden |
| Production | Not approved | No-go | No-go | No-go | Blocked |
| Real data | Not approved | No-go | No-go | No-go | Blocked |

## Conclusion

Contract and passive schema are allowed.

Runtime extraction, automatic finding creation, AI/OCR runtime, production and real-data use remain no-go.

