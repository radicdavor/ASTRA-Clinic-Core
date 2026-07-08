# Program 1 Phase D87 - Next-Step Decision Brief

Status: recommended path selected

## Option A

`Program 1 Phase D88 - Open Question Persistence Design`

Documentation-only. Define persistence shape, source-linking, lifecycle fields and review boundaries before any DB model or migration.

## Option B

`Program 1 Phase D88 - Findings Review Workflow Contract`

Documentation-only. Define review semantics without adding a review endpoint or workflow.

## Option C

`Program 1 Phase D88 - ClinicalDocument Extraction Candidate Review Workspace Contract`

Documentation-only. Define review workspace boundaries without extraction runtime or AI/OCR.

## Recommendation

Choose Option A: `Program 1 Phase D88 - Open Question Persistence Design`.

Open questions now have contract, passive schema and no-go guards. Persistence design is the lowest-risk next step because it can clarify source-linking and status shape before any runtime endpoint, automatic creation or UI appears.

## Non-Goals

- no open question endpoint
- no open question DB model or migration in this decision
- no automatic question creation
- no Task engine
- no Outcome Evidence
- no patient messaging
- no diagnosis or treatment automation
- no production or real-data approval
