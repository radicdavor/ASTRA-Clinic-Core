# Transaction Boundaries

Service functions should not commit.

Endpoints own the final transaction boundary:

1. validate request and permissions
2. call service functions
3. write audit records
4. commit once

If any step fails, the request should roll back.

## Critical Atomic Workflows

- appointment completion with material consumption
- purchase order receiving
- invoice issuing
- invoice payment
- stock transfer, adjustment and write-off

## Current Test Coverage

The V4 tests cover:

- insufficient stock leaves batch quantities unchanged
- failed purchase receiving does not create batches or movements
- overpayment does not alter invoice status
- mark-paid does not duplicate payments

Future tests should add full HTTP-level rollback checks for appointment material consumption.
