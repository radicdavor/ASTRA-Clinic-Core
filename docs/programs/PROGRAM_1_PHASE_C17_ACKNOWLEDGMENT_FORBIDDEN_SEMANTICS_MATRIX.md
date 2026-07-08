# Program 1 Phase C17 - Acknowledgment Forbidden Semantics Matrix

Status: documentation-only matrix

## Purpose

This matrix separates safe review vocabulary from forbidden approval, clearance and override semantics.

| Term | Allowed term | Allowed runtime effect | Allowed UI label | Audit implication | No-go reason | Future review needed |
| --- | --- | --- | --- | --- | --- | --- |
| reviewed | yes | no status change | Pregledano | may record human review event | must not imply approval | yes |
| acknowledged | conditional | no status change | Pregled signala evidentiran | may record reason and context | must not resolve readiness risk alone | yes |
| approved | no | no | no | no | implies clinical approval | yes |
| cleared | no | no | no | no | implies readiness clearance | yes |
| overridden | no | no | no | no | implies override workflow | yes |
| resolved | no | no | no | no | can imply risk removed | yes |
| patient ready | no | no | no | no | implies readiness decision | yes |
| procedure approved | no | no | no | no | implies procedure authorization | yes |
| task created | no | no | no | no | Task engine is out of scope | yes |
| message sent | no | no | no | no | patient messaging is out of scope | yes |
| outcome evidence recorded | no | no | no | no | Outcome Evidence is out of scope | yes |
| appointment status changed | no | no | no | no | would mutate operational workflow | yes |

## Conclusion

Only reviewed or acknowledged vocabulary may be considered in future phases.

Approval, clearance and override vocabulary remains forbidden.

Acknowledgment alone cannot resolve readiness risk.

