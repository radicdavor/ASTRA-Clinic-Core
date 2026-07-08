# Program 1 Phase D69 - Extraction Confidence and Limitations Contract

Status: confidence and limitations contract

## Purpose

Define how confidence and limitations may be represented for extraction candidates.

## Confidence

Confidence is advisory metadata about extraction quality.

It is not:

- clinical certainty
- diagnosis confidence
- treatment confidence
- permission to persist automatically
- permission to notify a patient

## Safe Confidence Labels

Allowed future labels:

- `unknown`
- `low`
- `medium`
- `high`

Even `high` confidence remains subject to human review.

## Limitations

Limitations must capture uncertainty such as:

- source not reviewed
- missing source span
- ambiguous wording
- conflicting source
- low OCR quality if OCR is later added
- AI extraction uncertainty if AI is later added
- external author or date unknown

## Handling Uncertainty

Low, missing, ambiguous or conflicting source confidence must keep candidate findings review-required.

No confidence level may trigger automatic clinical decisions.

