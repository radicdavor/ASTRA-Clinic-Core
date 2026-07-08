# Program 1 Phase U2 - Clinical Responsibility Static Control

Phase U does not assign legal/clinical responsibility to the system.

Phase U does not authorize clinical use.

Phase U does not create autonomous diagnosis or treatment behavior.

| Control Element | Purpose | Static Artifact | Runtime Implementation? | Required Future Implementation, If Any | Required Future Validation | Current Limitation | Explicit Prohibition Still Active |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clinical owner type | define future accountability | owner type statement | no | owner assignment process | owner review | no named owner assigned | no clinical approval |
| clinician final authority | preserve human authority | responsibility statement | no | clinical workflow design if approved | clinical safety validation | no clinical workflow | no autonomous decision |
| advisory-only system role | prevent decision claims | advisory language standard | no | UI/API wording checks | wording validation | static only | no diagnosis/treatment automation |
| human-in-the-loop requirement | require human interpretation | human review boundary | no | review workflow if approved | workflow validation | no runtime enforcement | no automatic review completion |
| no autonomous diagnosis | block diagnosis automation | prohibition entry | no | negative tests if runtime added | no-go validation | static only | no autonomous diagnosis |
| no autonomous treatment | block treatment automation | prohibition entry | no | negative tests if runtime added | no-go validation | static only | no autonomous treatment |
| manual review expectation | state review need | policy note | no | future review process | review evidence | no active process | no clinical signoff |
| clinical safety escalation concept | define escalation idea | U6 static model | no | incident workflow if approved | tabletop drill | no live incident system | no operational readiness |
| non-production boundary | prevent production inference | non-approval registry | no | production gate if approved | evidence review | static only | no production use |
| real-data non-approval boundary | prevent real-data inference | non-approval registry | no | real-data controls if approved | legal/privacy review | static only | no real patient data |
