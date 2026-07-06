# Codex Instructions for ASTRA Clinic Core

Before any code, schema, API, UI, module, documentation workflow, or AI-agent implementation change, read:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`

That document is the highest architectural level of the project.

All future decisions must comply with it.

## Pre-Implementation Check

Before implementing any change, verify:

1. Is the change aligned with ASTRA's philosophy?
2. Does it make the system simpler, or does it only add more features?
3. Can it be implemented inside the existing Clinic Core model?
4. Does it preserve the unified system language?
5. Does it respect security, audit and AI rules?

If a requested feature is not aligned with the Architecture Bible, do not implement it without first explaining the conflict.

## Architecture Bible Changes

Do not edit `docs/ASTRA_ARCHITECTURE_BIBLE.md` directly unless the maintainer explicitly asks for that exact edit.

If development reveals that the Architecture Bible should be expanded or clarified, create or update:

- `docs/ARCHITECTURE_CHANGE_PROPOSAL.md`

The proposal must explain:

- what should change
- why the change is needed
- which current project decision exposed the gap
- what risk exists if the Bible is not clarified

The Architecture Bible is not static, but it changes only deliberately and by maintainer decision.

## Design Constraints

All new functionality, APIs, modules, UI components and AI agents must follow the Architecture Bible principles:

- human above software
- one source of truth
- one shared language
- modular Clinic Core
- API First
- AI as assistant, never decision-maker
- audit for all important changes
- demo/real-data safety by default

