# Program 1 Phase C128 - Acknowledgment Write Endpoint Risk Register

Status: risk register

## Purpose

This register documents risks that block a Human Review Acknowledgment write endpoint during Phase C.

Acknowledgment means only that a human reviewed advisory context. It must not be treated as clinical approval, readiness clearance, override, task completion, Outcome Evidence or appointment status control.

## Risk Register

| Risk | Description | Severity | Likelihood | Mitigation | Current Status | Go/No-Go Impact |
| --- | --- | --- | --- | --- | --- | --- |
| Soft clearance interpretation | Staff may treat acknowledgment as permission to proceed. | High | High | Keep write endpoint no-go; use explicit no-clearance wording. | Open | Blocks write endpoint |
| Staff overreliance | Users may rely on an acknowledgment instead of reviewing source-linked findings. | High | Medium | Build Findings Lifecycle before write action. | Open | Blocks write endpoint |
| False reassurance | A stored acknowledgment may imply risk has been handled. | High | Medium | Avoid resolution language and action buttons. | Open | Blocks write endpoint |
| Alert fatigue | Repeated advisory prompts and acknowledgments can become routine clicks. | Medium | Medium | Do not add UI action before lifecycle design. | Open | Blocks UI action |
| Acknowledgment treated as resolution | A review note may be interpreted as closing an issue. | High | High | Define findings statuses before write workflow. | Open | Blocks write endpoint |
| Clinician responsibility ambiguity | The actor's responsibility may be unclear without a lifecycle model. | High | Medium | Document human responsibility and D0 scope. | Open | Blocks write endpoint |
| Patient harm through ignored signal | A user may acknowledge without addressing a relevant risk. | High | Medium | Keep acknowledgment non-actionable and read-only. | Open | Blocks write endpoint |
| Audit overload | Write/read audit events may obscure important signals. | Medium | Medium | Keep successful reads unaudited; denied-read only. | Mitigated for reads | Blocks broader audit rollout |
| UI pressure to add action button | A write endpoint would invite button-driven workflows. | Medium | High | Final UI action no-go. | Open | Blocks UI action |
| Role/permission misuse | Broad write permissions could allow unsafe actors to acknowledge. | High | Medium | Keep write permission seed absent. | Open | Blocks permission seed |
| API misuse | API clients could bulk-write acknowledgments. | High | Medium | No endpoint; API keys denied for read and no write scope. | Open | Blocks endpoint |
| Real-data privacy exposure | Acknowledgments may contain review context tied to real patients. | High | Medium | Real patient data remains no-go. | Open | Blocks real-data use |
| Production claim creep | A working write endpoint may be mistaken for production readiness. | High | Medium | Keep production no-go docs current. | Open | Blocks production |
| Legal/compliance ambiguity | Meaning and retention of acknowledgment writes remain underdefined. | High | Medium | Defer write endpoint pending legal/compliance review. | Open | Blocks write endpoint |
| Lack of Findings Lifecycle foundation | ASTRA lacks a stable finding lifecycle to attach review actions to. | High | High | Proceed to D0 before any write endpoint. | Open | Blocks write endpoint |

## Current Mitigations

- no POST/PATCH/PUT/DELETE acknowledgment route
- no frontend write client
- no UI action button
- no write permission seed
- read-only UI copy states acknowledgment is not approval and does not change appointment status
- selective denied-read audit only
- successful list/detail reads remain unaudited

## Conclusion

The risk register supports a final Phase C No-Go for an acknowledgment write endpoint.

The recommended mitigation path is `Program 1 Phase D0 - Findings Lifecycle Foundation`.

