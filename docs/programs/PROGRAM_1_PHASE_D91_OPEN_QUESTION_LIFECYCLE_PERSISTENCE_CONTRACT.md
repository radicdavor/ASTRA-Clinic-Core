# Program 1 Phase D91 - Open Question Lifecycle Persistence Contract

Status: design only

## Safe Status Values

- `draft`
- `suggested`
- `awaiting_review`
- `under_review`
- `needs_clinician_decision`
- `decision_documented`
- `deferred`
- `closed_for_now`

## Storage Policy

Future persistence must store one safe status value per open question. The status must be constrained to the safe taxonomy and must not use approval, clearance, override, diagnosis, treatment, task, outcome or patient notification vocabulary.

## Transition Boundaries

- `reviewed` semantics should be expressed through review metadata, not unsafe resolution wording
- `decision_documented` means a human decision may be documented elsewhere; it does not create the decision by itself
- `deferred` means the question remains intentionally not acted on now; it does not mean safe or resolved
- `closed_for_now` is not permanent episode closure and must not close care automatically

## Forbidden Runtime Effects

Status persistence must not:

- create a Task
- create Outcome Evidence
- message a patient
- confirm diagnosis or treatment
- close an episode automatically
- change appointment status
- approve, clear or override readiness
