# Current product state

This is the canonical user-visible product-state source. Program phase files are historical implementation evidence.

## Current workflows and roles

ASTRA Clinic Core provides a synthetic/demo workflow for patients, appointments, the daily clinic list, canonical patient journeys, preparation, documents, reception check-in, encounter notes, consumables, invoice/payment and audit. Primary navigation is **Danas, Pacijenti, Naručivanje, Znanje** with role-filtered tools under **Više**.

Roles are administrator, physician, nurse/technician, receptionist, billing, inventory manager, AI service account and document reviewer. Backend permissions, not frontend visibility, are authoritative.

Primary routes: `/`, `/patients`, `/appointments`, `/journeys/:id`, `/reception`, `/clinical-documents`, `/laboratory`, `/therapies`, `/knowledge`, `/workflow`, `/inventory`, `/invoices`, `/audit-log`, `/readiness`. Administration includes services, clinics/staff, modules and API keys.

## Capability disposition

- Implemented: canonical journey, role-aware dashboard/workspace, local uploads/source viewing, check-in, encounter, consumables, local invoice/payment records, RBAC and audit.
- Demo/test: deterministic summary, text-only OCR, metadata classification, reminder sender, synthetic accounts/data and noop fiscalization.
- Disabled: AI diagnosis suggestions by default; disabled capabilities fail closed.
- Contract only: public web intake, AI secretary, mailbox and scanner-driver boundaries.
- Not authorized: real data, live external providers, public booking, production deployment, fiscalization, payment terminal and go-live.

## Current readiness decision

The technical candidate may be prepared only for **human synthetic usability evaluation** after all repository gates pass. Human evidence has not been claimed. Pilot readiness does not authorize pilot execution. Deployment status remains local/controlled demo only.
