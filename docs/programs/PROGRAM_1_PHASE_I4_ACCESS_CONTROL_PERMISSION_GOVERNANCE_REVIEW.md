# Program 1 Phase I4 - Access-Control Permission Governance Review

## Current Read Permissions

The foundation includes read permissions for sensitive clinical read surfaces such as findings, open questions and timeline views.

## Intentionally Absent

- write permissions for findings/open questions/timeline
- review/approve/clear/resolve permissions
- Task or Outcome Evidence permissions
- patient messaging permissions
- AI/system write permissions

## API Key Boundary

API keys remain restricted for sensitive clinical surfaces. API key access must not imply clinician review, write access, approval, clearance or decision authority.

## Role Boundary

- physicians: future clinical interpretation candidates, not automatic decision engines
- admins: operational administration, not clinical interpretation by default
- nurses/reception: limited access according to future policy
- AI agents/system jobs: denied by default for clinical write/review workflows

## Future Approval Process

Any new permission must include design, safety review, tests, least-privilege rationale and explicit maintainer approval.

