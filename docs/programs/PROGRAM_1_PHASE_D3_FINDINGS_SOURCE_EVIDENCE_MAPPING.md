# Program 1 Phase D3 - Findings Source Evidence Mapping

Status: source evidence mapping

## Purpose

Every finding must remain source-linked.

The source link is what allows a human reviewer to evaluate context instead of treating a derived statement as self-evident truth.

## Required Source Fields

Future finding records or schemas should be able to represent:

- source document reference
- source type
- source date if known
- source author or institution if known
- source label/title
- extraction method
- reviewed/unreviewed source boundary
- confidence or limitation text
- source reference path or item key

## Source Types

Expected source families include:

- uploaded PDF
- internal clinical note
- external report
- lab result
- pathology report
- endoscopy report
- radiology report
- referral or discharge letter
- physician-entered note

## Extraction Boundary

Extraction may be manual, placeholder or future AI/OCR.

Extraction is not clinical truth.

AI extraction may propose structure, but source-linked findings require human review before they become official clinical knowledge.

## Reviewed / Unreviewed Boundary

Findings from unreviewed sources must remain marked as requiring review.

A finding derived from a reviewed source still does not become diagnosis, treatment plan, Task, Outcome Evidence or patient message by itself.

## Limitations

Each finding should carry limitations such as:

- source not fully reviewed
- source date unknown
- external author unknown
- extraction confidence unknown
- source contradicts another source
- missing follow-up document

## Runtime Boundary

D3 does not implement real AI/OCR, extraction engine, finding endpoint, DB persistence or UI.

