# Program 1 Phase M4 - Sequencing and Dependency Plan

Recommended sequencing:

## M Completed - Remediation Planning Only

Purpose: map gaps into workstreams.

Inputs: Phase L gap review.

Outputs: remediation plan.

Non-approval: no production or real-data approval.

Dependencies: none.

Must not implement: runtime controls or clinical workflows.

## N - Governance Control Design

Purpose: design responsibility boundaries, review gates, non-approval controls and escalation requirements.

Inputs: Phase M plan.

Outputs: governance control design.

Non-approval: design is not implementation or approval.

Dependencies: Phase M.

Must not implement: approval/clearance/override runtime.

## O - Real Patient Data Governance Design

Purpose: design real-data, GDPR/DPIA, retention, export and incident policies.

Inputs: Phase M and legal/privacy requirements.

Outputs: real-data governance design.

Non-approval: no real data allowed.

Dependencies: Phase N governance boundaries.

Must not implement: real-data enablement.

## P - Access Control and Auditability Design

Purpose: design least privilege and audit completeness.

Inputs: governance and real-data designs.

Outputs: access/audit design.

Non-approval: no permission expansion by itself.

Dependencies: Phase N/O.

Must not implement: new clinical write permissions.

## Q - Validation and Safety Test Plan

Purpose: design production validation evidence.

Inputs: safety, access and audit designs.

Outputs: validation matrix.

Non-approval: test plan is not validation completion.

Dependencies: Phase N/P.

Must not implement: production deployment.

## R - Operational Readiness and Incident Response Plan

Purpose: design operations, monitoring, rollback and incident response.

Inputs: validation and governance plans.

Outputs: operations readiness plan.

Non-approval: operations plan is not go-live.

Dependencies: Phase Q.

Must not implement: production exposure.

## S - Demo Operations Pack or Controlled Pilot Preparation

Purpose: prepare non-production demo or controlled pilot materials.

Inputs: governance, validation and operations plans.

Outputs: demo/controlled pilot operation pack.

Non-approval: controlled demo/pilot is not production.

Dependencies: Phase N-R.

Must not implement: real patient data use or write clinical workflows.
