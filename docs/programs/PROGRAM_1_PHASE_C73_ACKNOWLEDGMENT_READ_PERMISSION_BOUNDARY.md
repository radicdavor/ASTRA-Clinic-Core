# Program 1 Phase C73 - Acknowledgment Read Permission Boundary

Status: permission boundary

## Future Read Permission

Canonical read permission:

`clinical_readiness.acknowledgments.read`

## Demo/Pilot Role Expectations

Allowed in guarded demo/pilot:

- admin
- physician

Not granted by default in this phase:

- nurse
- receptionist
- billing
- inventory manager
- AI agent
- API key runtime actor

## Separation From Write

Read permission does not imply:

- acknowledgment creation
- acknowledgment update
- acknowledgment deletion
- approval
- clearance
- override
- appointment status mutation

Write permissions remain no-go:

- `clinical_readiness.acknowledgments.write`
- `clinical_readiness.acknowledgments.manage`

## API Key and AI Restrictions

API keys and AI agents must not read acknowledgments by default.

Any future API access requires separate governance.

## Zakljucak

Read permission may be seeded only for read-only prototype support.

Write permission remains forbidden.

