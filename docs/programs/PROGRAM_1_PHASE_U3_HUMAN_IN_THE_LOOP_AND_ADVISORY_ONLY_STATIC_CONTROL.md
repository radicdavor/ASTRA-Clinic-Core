# Program 1 Phase U3 - Human-in-the-Loop and Advisory-Only Static Control

| Boundary | Required Static Language/Control | Current Status | Runtime Implementation? | Required Future Validation | Explicit Prohibition Still Active |
| --- | --- | --- | --- | --- | --- |
| advisory-only language standard | use not a clinical decision / requires clinician review | static control documented | no | wording scan and clinical review | no diagnosis/treatment automation |
| human review requirement | require human interpretation before clinical action | static control documented | no | workflow validation if implemented | no automatic review completion |
| no autonomous clinical decision | state system does not decide care | static control documented | no | negative tests | no autonomous clinical decision |
| no automatic treatment recommendation | state no automatic treatment plan | static control documented | no | negative tests | no treatment automation |
| no patient-facing autonomous message | state no patient message is sent | static control documented | no | messaging no-go tests | no patient messaging |
| no appointment mutation | state status is not changed | static control documented | no | route/UI no-go tests | no appointment mutation |
| no workflow enforcement | state no workflow is enforced | static control documented | no | workflow no-go tests | no workflow enforcement |
| no approval/clearance/override | state no approval, clearance or override exists | static control documented | no | no-go tests | no approval/clearance/override |
| operator disclaimer requirement | require demo/non-production disclaimer | static control documented | no | demo review | no production claim |
| known limitations visibility | keep limitations linked and visible | static control documented | no | docs/UI review | no maturity overclaim |
