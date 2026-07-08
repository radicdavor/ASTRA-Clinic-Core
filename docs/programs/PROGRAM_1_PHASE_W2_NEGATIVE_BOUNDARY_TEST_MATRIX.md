# Program 1 Phase W2 - Negative Boundary Test Matrix

The future negative test matrix must prove that prohibited categories stay prohibited in non-production prototype layers.

| Negative test | Protected boundary | Expected future assertion | Current status |
| --- | --- | --- | --- |
| mark real patient data as allowed | real-data no-go | rejected/prohibited | planned only |
| mark PHI/PII as allowed | PHI/PII no-go | rejected/prohibited | planned only |
| mark production operation as allowed | production no-go | rejected/prohibited | planned only |
| mark patient messaging as allowed | messaging no-go | rejected/prohibited | planned only |
| mark appointment mutation as allowed | appointment mutation no-go | rejected/prohibited | planned only |
| mark clinical write workflow as allowed | clinical write no-go | rejected/prohibited | planned only |
| mark approval/clearance/override as allowed | approval boundary | rejected/prohibited | planned only |
| mark Task engine as allowed | Task engine no-go | rejected/prohibited | planned only |
| mark Outcome Evidence as allowed | Outcome Evidence no-go | rejected/prohibited | planned only |
| mark workflow enforcement as allowed | workflow enforcement no-go | rejected/prohibited | planned only |
| infer approval from a tag, doc, or prototype | non-approval boundary | rejected by wording and future assertion | planned only |

No negative test in this matrix authorizes a prohibited category. Passing a future negative test would only show that the prototype remained non-authorizing under that test condition.
