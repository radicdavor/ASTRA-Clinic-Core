# Program 1 Phase C93 - Acknowledgment Read UI Usability Review Plan

Status: usability review plan

## Purpose

C93 defines the review criteria for the read-only Human Review Acknowledgment panel in Appointment Workspace.

The review is limited to readability, safety wording, empty/error behavior and no-action boundaries.

This phase does not authorize acknowledgment write actions, runtime enforcement, clinical approval, readiness clearance, override behavior, production use or real patient data.

## User Roles

Primary review roles:

- physician reviewing advisory context
- admin validating demo/pilot workflow safety

Secondary roles:

- nurse or receptionist with limited read visibility, only where permissions allow

API keys, AI agents and system jobs are not human reviewers for this UI.

## Read-Only Expectations

The panel may display existing acknowledgment records.

The panel must not provide:

- acknowledgment action button
- approve or clear action
- override action
- task creation
- patient message action
- appointment status action

## Safety Wording Criteria

Required wording themes:

- this is a human review record
- this is advisory context
- it is not clinical approval
- it does not change appointment status
- it does not send a patient message
- clinical interpretation remains a physician responsibility

Forbidden wording:

- odobreno
- clearance
- cleared
- override
- rijeseno
- resolved
- pacijent spreman
- postupak odobren
- task created
- poslano pacijentu

## Empty State Criteria

The empty state must say that no saved human review records exist for the appointment.

It must not imply:

- no readiness questions exist
- patient is ready
- procedure is approved
- advisory signals are resolved

## Loading and Error State Criteria

Loading must be neutral and non-blocking.

Error state must say records are unavailable without implying clinical readiness was confirmed or denied.

The rest of Appointment Workspace must remain usable according to the user's permissions.

## Permission Denied Criteria

Permission denied must be local to the acknowledgment panel.

It must not imply:

- approval was denied
- clearance was denied
- patient is blocked
- workflow enforcement occurred

## Timestamp, Actor and Reason Display Criteria

The UI must show:

- created timestamp
- actor role
- actor user id when available
- reason as a review note

The reason must not be displayed as a clinical conclusion.

The actor must not be described as an approver, clearer or override authority.

## Snapshot and Advisory Relation Criteria

The UI may show:

- advisory signal key
- optional snapshot relation

Safe snapshot labels:

- Povezano sa snapshot zapisom
- Snapshot ostaje nepromijenjen
- Pregled ne mijenja spremljeni snapshot

The UI must not imply the snapshot or advisory signal was corrected, approved, cleared, overridden or resolved.

## No-Action Criteria

The panel must remain display-only.

Any future action must go through a separate go/no-go review before implementation.

## Demo/Pilot Assumption

C93 remains guarded demo/pilot work.

Real patient data and production use remain no-go.

