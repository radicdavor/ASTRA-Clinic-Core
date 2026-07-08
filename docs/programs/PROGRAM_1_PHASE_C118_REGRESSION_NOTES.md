# Program 1 Phase C118 - Regression Notes

Status: permission denied read audit implemented

## Implemented

- acknowledgment list/detail read endpoints now use explicit actor handling
- authenticated user without read permission writes one denied-read audit event
- API key read attempt writes one denied-read audit event
- successful list/detail reads remain unaudited

## Runtime Boundary

Denied-read audit is access/security evidence only.

No write endpoint, UI action, approval, clearance, override, Task, Outcome Evidence, appointment status mutation or patient messaging was added.

