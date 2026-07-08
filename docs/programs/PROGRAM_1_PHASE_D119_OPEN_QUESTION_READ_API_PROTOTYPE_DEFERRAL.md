# Program 1 Phase D119 - Open Question Read API Prototype Deferral

Status: deferred

## Deferral Decision

The open question read API prototype is deferred to a later explicit phase. D110-D120 defines the contract, response shape, permission boundary, error states, audit policy and no-go guard only.

## Why Endpoint Implementation Is Deferred

- Permission seed policy needs a separate implementation decision.
- Source-linked response behavior should be verified against the DB foundation before runtime exposure.
- Audit policy remains documentation-only and should not be coupled accidentally to first endpoint implementation.
- Frontend UI/client is out of scope for this phase.
- Open questions must not become a shortcut to review, approval, clearance, diagnosis, treatment or automatic question creation.

## Prerequisites Before a GET Endpoint

- Explicit phase selecting GET-only prototype.
- Read permission seed decision.
- Patient-scoped list and detail tests.
- Source-linked response tests.
- Forbidden field absence tests.
- Route absence tests for POST, PATCH, PUT, DELETE, review, approve, clear and resolve.
- Side-effect-free read tests.
- Audit behavior decision, including denied-read policy if selected.

## Current No-Go Boundary

No endpoint, service, frontend client, UI, permission seed, audit write or automatic question creation is added in D119.

## Future Candidate

Program 1 Phase D121 or later may implement a GET-only prototype if the no-go guards remain clean.
