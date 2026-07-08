# Program 1 Phase C21 - Advisory Read-Only UI Surface Design

Status: design-only UI contract

## Purpose

This document defines a read-only Advisory Signal surface for Appointment Workspace.

The surface helps humans notice review signals without creating enforcement behavior.

## Placement

Preferred placement:

- Appointment Workspace
- near Clinical Readiness Preview
- before snapshot history

The surface may derive from existing read-only preview data.

## Required Labels

Allowed labels:

- `Savjetodavni signali`
- `Za ljudski pregled`
- `Nije klinicko odobrenje`
- `Ne mijenja status termina`
- `Non-blocking signal`

## Helper Text

Required helper meaning:

- advisory signal is informational
- it is for human review
- it does not approve, clear or block workflow
- it does not change appointment status
- source and limitations should be checked

## Empty State

Safe empty state:

`Nema savjetodavnih signala u trenutnom previewu.`

This must not mean patient is ready.

## Missing Data State

Safe missing data state:

`Savjetodavni signali trenutno nisu dostupni jer preview nije ucitan.`

This must not mean patient is safe, unsafe, cleared or approved.

## Warning State

Warnings may be shown as review prompts only.

They must not create automatic blocking or rescheduling behavior.

## Forbidden Actions

The read-only surface must not include:

- acknowledgment button
- approve button
- clear button
- override button
- task creation
- patient messaging
- appointment status mutation

## Relationship To Snapshot Detail And History

Snapshot history and detail remain saved preview records.

Advisory surface may show the current live preview, but it must not rewrite historical snapshots.

## Relationship To Physician Review

The surface may help physicians notice what requires review.

It must not claim that review happened.

It must not record review.

It must not replace physician judgment.

