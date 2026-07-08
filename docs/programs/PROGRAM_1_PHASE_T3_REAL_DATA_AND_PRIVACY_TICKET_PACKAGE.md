# Program 1 Phase T3 - Real-Data and Privacy Ticket Package

No DATA or LEGAL ticket authorizes real patient data use.

All DATA and LEGAL tickets are future preparation/control tickets only.

| Ticket ID | Title | Purpose | Source Phases | Risk Class | Blocking Status | Owner Type | Reviewer Types | Prerequisites | Acceptance Criteria | Required Validation Evidence | Required Negative Tests | Explicit Out-of-Scope Items | Non-Approval Statement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DATA-001 | PHI/PII classification implementation package | classify sensitive data | O,S | R0 | blocks real data | Data governance owner | Legal, privacy | O1 | classification policy defined | classification review | unclassified-data examples | PHI processing | not PHI approval |
| DATA-002 | Synthetic-vs-real data boundary implementation package | prevent demo/real mixing | O,Q,S | R0 | blocks real data | Data/product owner | Privacy, QA | DATA-001 | boundary controls defined | data audit evidence | real-like demo records | synthetic data creation that looks real | not real-data approval |
| DATA-003 | Real-data ingestion prohibition/control package | block real data entry | O,Q,S | R0 | blocks real data | Privacy/security owner | QA, legal | DATA-001 | ingestion blocked or gated | negative test evidence | PHI/PII entry attempts | ingestion runtime approval | not ingestion authorization |
| DATA-004 | Consent/legal basis evidence package | define legal basis evidence | O,S | R0 | blocks real data | Legal/compliance owner | Privacy, product | legal review plan | evidence package defined | legal review record | missing basis scenarios | legal determination | not legal approval |
| DATA-005 | Retention/deletion/export design-to-implementation package | govern lifecycle | O,S | R0 | blocks real data | Data/legal owner | Security, QA | DATA-004 | lifecycle procedures defined | lifecycle tests | unauthorized export/delete attempts | export/delete runtime approval | not lifecycle approval |
| DATA-006 | Environment separation real-data control package | isolate environments | O,R,S | R0 | blocks real data and production | Security/operations owner | Engineering, privacy | DATA-001 | environment separation defined | isolation tests | demo/real mix attempts | production deployment | not environment approval |
| DATA-007 | DPIA/GDPR review preparation package | prepare compliance review | O,S | R0 | blocks real data | Privacy/legal owner | Data, security | DATA-004 | DPIA/GDPR package prepared | legal review evidence | missing DPIA inputs | GDPR compliance claim | not GDPR approval |
| LEGAL-001 | DPA/vendor/subprocessor review package | govern vendors | O,R,S | R0 | blocks vendor processing | Legal/privacy owner | Security, operations | vendor inventory | DPA review package defined | vendor review evidence | unreviewed vendor scenarios | vendor approval | not DPA approval |
| LEGAL-002 | Breach notification procedure package | prepare breach response | O,R,S | R1 | blocks incident readiness | Legal/security owner | Privacy, operations | incident model | breach procedure defined | tabletop evidence | breach triage scenarios | live breach process | not breach readiness |
