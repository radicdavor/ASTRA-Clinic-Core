# V19 Architecture Bible Compliance Gate

## Status

Implemented as project governance.

## Purpose

V19 turns `docs/ASTRA_ARCHITECTURE_BIBLE.md` from a reference document into an active development gate.

The goal is not to slow development. The goal is to keep ASTRA coherent:

- human above software
- one source of truth
- one shared language
- stable Clinic Core
- API First
- AI as assistant
- audit for important changes
- demo/real-data safety by default

## Required Check Before Implementation

Before any code, schema, API, UI, module, documentation workflow or AI-agent change, the implementer must answer:

1. Is the change aligned with ASTRA's philosophy?
2. Does it make the system simpler, or does it only add more functions?
3. Can it be implemented inside the existing Clinic Core model?
4. Does it preserve the unified system language?
5. Does it respect security, audit and AI rules?

If any answer is `No` or unclear, the change must not proceed until the architectural conflict is explained.

## Change Categories

Every change should identify its category:

- Information: does not change data.
- New object: creates data.
- Update: changes existing data.
- Critical action: irreversible or hard-to-reverse change; requires warning, confirmation and audit.
- AI action: must be clearly marked as AI-assisted and must not make medical decisions.

## Architecture Bible Changes

Do not edit `docs/ASTRA_ARCHITECTURE_BIBLE.md` directly unless the maintainer explicitly requests that exact edit.

If a gap is found, create or update:

- `docs/ARCHITECTURE_CHANGE_PROPOSAL.md`

The proposal must explain:

- what should change
- why the change is needed
- which project decision exposed the gap
- what risk exists if the Bible is not clarified

## Enforcement Points

V19 adds these enforcement points:

- `AGENTS.md` requires reading the Architecture Bible before implementation.
- `docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md` records the Codex workflow rule.
- `.github/pull_request_template.md` requires a short Architecture Bible check for PRs.
- `docs/RELEASE_CHECKLIST.md` includes Architecture Bible compliance.
- `docs/MANUAL_QA_CHECKLIST.md` includes UI language, contextual help and safety checks.
- `scripts/validate_pilot_release.sh` verifies that the core governance files exist and are linked.

## Design-System Addendum

`docs/CODEX_MASTER_PROMPT_V19.md` also introduced a design-system consistency sprint. The implementation is documented in:

- `docs/ASTRA_DESIGN_SYSTEM.md`
- `docs/V19_IMPLEMENTATION_REPORT.md`
- `docs/ARCHITECTURE_CHANGE_PROPOSAL_PATIENT_IDENTITY_AND_ACTION_LANGUAGE.md`

## Definition of Done

V19 is complete when:

- Architecture Bible is linked from README.
- Codex instructions require reading it before changes.
- PRs include an Architecture Bible check.
- Release and QA checklists include architecture compliance.
- A proposal path exists for future Bible changes.
- Pilot validation script verifies the governance files.

