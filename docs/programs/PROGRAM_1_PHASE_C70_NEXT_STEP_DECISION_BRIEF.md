# Program 1 Phase C70 - Next-Step Decision Brief

Status: decision brief

## Option A

`Program 1 Phase C71 - Acknowledgment Read API Contract Design`

Recommended.

Reason:

Before write endpoint work, ASTRA should define how acknowledgments are safely read, displayed and audited without implying resolution.

## Option B

`Program 1 Phase C71 - Acknowledgment Write Endpoint Implementation Gate`

Not recommended yet.

Reason:

Idempotency storage, permission UX and read model are not mature enough for write endpoint rollout.

## Option C

Pause acknowledgment and return to Patient Clinical Knowledge hardening.

Allowed if maintainer wants to reduce Program 1 scope.

## Recommendation

Proceed with Option A.

Expected next task:

`Program 1 Phase C71 - Acknowledgment Read API Contract Design`

The next phase should remain contract-first and should not add write endpoints.

