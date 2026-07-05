# Billing Workflow

ASTRA Clinic Core separates draft billing from issued invoice numbering.

## Draft

- Draft invoices can be created manually or from an appointment.
- Draft invoices use temporary `DRAFT-*` numbers.
- Draft invoice lines can be added, updated and deleted.

## Issue

`POST /api/invoices/{invoice_id}/issue` converts a draft invoice into an issued invoice.

Rules:

- only `draft` invoices can be issued
- the invoice must have at least one line
- the invoice total must be positive
- official invoice numbers use `invoice_number_sequences`
- official numbers are unique and allocated inside the database transaction

## Payments

Payments are separate `PaymentTransaction` records.

Rules:

- only issued and partially paid invoices can receive payments
- draft, cancelled and already paid invoices cannot receive payments
- overpayment is rejected
- partial payment sets `payment_status=partially_paid`
- full payment sets `payment_status=paid`
- `mark-paid` creates only the remaining payment amount and does not double count existing payments

Fiscalization is intentionally not implemented yet. The current code only prepares the workflow and fields needed for a later adapter.
