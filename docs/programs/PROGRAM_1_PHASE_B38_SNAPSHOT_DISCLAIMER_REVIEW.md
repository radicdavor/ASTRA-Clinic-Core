# Program 1 Phase B38 - Snapshot Disclaimer Review

Status: legal/compliance wording review for demo/pilot snapshot layer

## Purpose

This document reviews Clinical Readiness Snapshot disclaimer wording before any future enforcement design.

It does not approve production use, real patient data or clinical enforcement.

## Required Disclaimer Meaning

Snapshot wording must communicate:

- demo/pilot context
- saved preview record
- not a medical decision
- not readiness clearance
- not clinical approval
- not Outcome Evidence
- physician remains responsible
- no real patient data approval

## Backend Canonical Disclaimer

The backend canonical disclaimer remains the source text stored with captured snapshots.

The frontend should display stored snapshot disclaimer rather than inventing a new clinical meaning.

## Frontend Safety Wording

Frontend helper text may use Croatian wording for readability, but must not change meaning.

Safe wording:

- snapshot zapis
- spremljeni preview zapis
- nije klinicko odobrenje
- ne mijenja status termina
- ne salje poruku pacijentu
- zamjena ne mijenja stari sadrzaj

Forbidden wording:

- approved
- cleared
- patient is ready
- procedure is approved
- final clinical decision
- override accepted
- Outcome Evidence
- Task created

## Physician Responsibility

The physician remains responsible for clinical decision-making.

Snapshot records may support review, but they do not decide.

## Real Patient Data

No real patient data approval is granted.

Before real data:

- legal review is required
- access-control review is required
- retention policy is required
- backup/restore drill is required
- maintainer approval is required

## Production Status

No production readiness is claimed.

## Recommended Next Task

`Program 1 Phase B39 - Snapshot Real-Data No-Go Checklist`
