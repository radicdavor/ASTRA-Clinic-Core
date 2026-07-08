# Program 1 Phase D5 - Findings Open Question Relationship

Status: relationship contract

## Purpose

This document defines how findings relate to open questions.

## Core Rule

A finding may open a question.

An open question is source-linked unresolved context. It is not a Task, diagnosis, treatment plan, patient instruction or automatic blocker.

## Safe Relationship

Finding -> Open Question means:

- source-linked information needs attention
- the clinical meaning is not fully resolved
- a physician decision may be required later
- the item should remain visible until reviewed or closed for now

It does not mean:

- automatic diagnosis
- task creation
- follow-up scheduling
- patient messaging
- Outcome Evidence
- episode closure

## Human Confirmation Boundary

An open question may become a recommendation later only by human confirmation under a future policy.

It must remain source-linked and auditable.

## Examples

### Pathology Dysplasia Question

A pathology report mentions dysplasia.

The finding may open a question about surveillance interval or treatment implications.

It is not automatically a diagnosis or treatment plan.

### Elevated Calprotectin Question

A lab source shows elevated calprotectin.

The finding may open a question about clinical context and further review.

It is not automatic inflammatory bowel disease diagnosis.

### Incomplete Colonoscopy Question

An endoscopy report states incomplete examination.

The finding may open a question about repeat procedure planning.

It does not automatically schedule a follow-up.

### Anticoagulant Ambiguity

Medication history suggests anticoagulant use is unclear.

The finding may open a readiness-related question.

It is not automatic clearance or procedure cancellation.

### Missing Histology Follow-Up

A procedure report references biopsies, but histology is missing.

The finding may open a missing-source question.

It is not Outcome Evidence and does not close care.

## Runtime Boundary

D5 does not implement open question endpoints, tasks, scheduling or messaging.

