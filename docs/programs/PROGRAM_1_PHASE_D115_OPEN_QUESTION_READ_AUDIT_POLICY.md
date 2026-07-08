# Program 1 Phase D115 - Open Question Read Audit Policy

Status: documented, not implemented

## Policy Decision

Successful list read audit is deferred by default to avoid audit noise.

## Read Categories

- successful list read: no audit by default
- successful detail read: future policy decision
- denied read: future candidate for selective access audit
- out-of-scope read: future candidate for selective access audit
- failed read: future policy decision based on risk and noise

## Payload Minimization

Future read audit payloads should avoid full clinical text, full source reference text and full open question label unless explicitly approved. Minimal payload candidates include actor, role, patient id, question id if safe, route/action, result category, request id and timestamp.

## Evidence Boundary

Read audit is access/security evidence only. It is not Outcome Evidence and must not be interpreted as clinical review, decision, diagnosis, treatment, approval, clearance or override.

## Current Phase Boundary

No read audit implementation is added in this phase.
