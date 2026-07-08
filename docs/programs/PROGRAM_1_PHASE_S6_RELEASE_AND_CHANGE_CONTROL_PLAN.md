# Program 1 Phase S6 - Release and Change-Control Plan

Phase S does not create an active release approval workflow.

Phase S does not authorize production releases.

Phase S only defines future release/change-control planning requirements.

| Control | Purpose | Required Owner Type | Required Evidence | Required Future Validation/Review | Current Status | Non-Approval Statement |
| --- | --- | --- | --- | --- | --- | --- |
| change request intake | capture proposed work | Product owner | request record | intake review | planned only | no active workflow |
| scope classification | classify risk | Product/security owner | classification record | scope review | planned only | no approval |
| safety boundary review | preserve no-go boundaries | Clinical/product owner | boundary checklist | clinical review | planned only | no safety sign-off |
| security/privacy review | review sensitive changes | Security/privacy owner | review record | security/privacy review | planned only | no security approval |
| clinical safety review | review clinical risk | Clinical owner | safety review | clinical review | planned only | no clinical approval |
| migration review | review DB changes | Engineering owner | migration plan | migration review | planned only | no migration approval |
| test evidence review | review test results | QA owner | test evidence | evidence review | planned only | no validation approval |
| negative test review | review no-go tests | QA/security owner | negative test evidence | negative review | planned only | no boundary validation |
| release notes | document release | Product owner | release notes | release review | planned only | no production claim |
| known limitations | document constraints | Product/legal owner | limitations doc | legal/product review | planned only | no live-use claim |
| rollback plan | define recovery | Operations/engineering owner | rollback plan | rollback review | planned only | no rollback validation |
| post-release verification | verify deployed state | Operations/QA owner | verification report | post-release review | planned only | no deployment approval |
| evidence archive | preserve proof | QA/operations owner | archive index | archive review | planned only | no evidence package |
| owner sign-off record | record review | Product owner | sign-off template | owner review | planned only | no sign-off granted |
| release freeze conditions | stop unsafe release | Release manager | freeze criteria | release review | planned only | no release freeze active |
| emergency change process | handle urgent changes | Operations/security owner | emergency process | tabletop review | planned only | no emergency workflow |
