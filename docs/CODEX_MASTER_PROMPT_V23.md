# Codex master prompt v23 - Pilot Release Candidate Sprint

Use this prompt after V22 Operational Evidence Loop has been implemented.

---

You are a senior full-stack architect, healthcare workflow designer, release engineer and product governance maintainer.

Before making changes, read:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md`
- `docs/ASTRA_DESIGN_SYSTEM.md`
- `docs/ASTRA_WORKSPACE_ARCHITECTURE.md`
- `docs/ASTRA_READINESS_MODEL.md`
- `docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`
- `docs/V0_1_GO_NO_GO_MATRIX.md`
- `docs/V0_1_PILOT_RELEASE_CHECKLIST.md`
- `docs/V0_1_TAG_READY.md`

## Sprint name

**Pilot Release Candidate Sprint**

## Main goal

Prepare ASTRA Clinic Core for an explicit `v0.1-pilot` release candidate decision without expanding product scope.

The sprint should make the pilot decision easier to inspect, validate and repeat:

`Readiness -> Pilot workflow -> Audit evidence -> Release candidate manifest -> Maintainer tag decision`

## Non-negotiable rules

- Do not enable real patient data.
- Do not implement real Croatian fiscalization.
- Do not add new clinical modules.
- Do not add Google Calendar/OpenEMR or other external integrations.
- Do not add AI receptionist or new AI mutation workflows.
- Keep demo warnings visible.
- Keep noop/stub fiscalization warning visible.
- Keep Architecture Bible stable unless the maintainer explicitly requests an edit.
- Do not create the `v0.1-pilot` tag without explicit maintainer approval.

## Phase 1 - Create release candidate manifest

Create:

`docs/V23_PILOT_RELEASE_CANDIDATE.md`

It must summarize:

- current candidate status
- required evidence files
- validation checks
- readiness expectations
- known non-blocking warnings
- blocker policy
- tag command and rollback reminder
- explicit statement that this is demo/pilot only

Acceptance criteria:

- The maintainer can open one file and understand what remains before tagging.

## Phase 2 - Validate release candidate artifacts

Update release validation so it checks:

- `docs/CODEX_MASTER_PROMPT_V23.md`
- `docs/V23_PILOT_RELEASE_CANDIDATE.md`
- V23 manifest mentions `v0.1-pilot`
- V23 manifest mentions `real_data_allowed=false`
- V23 manifest references readiness, CI and human pilot evidence

Acceptance criteria:

- CI or local validation catches missing V23 release candidate documents.

## Phase 3 - README visibility

Update README pilot documents so V23 release candidate status is discoverable.

Acceptance criteria:

- A maintainer starting from README can find the V23 release candidate manifest.

## Phase 4 - Do not overbuild

Only add code if it directly protects the release candidate decision.

Good candidates:

- validation scripts
- smoke tests
- release candidate documentation
- small readiness contract tests

No-go:

- new user-facing modules
- broad UI redesign
- production deployment claims
- real-data enablement

## Definition of done

This sprint is done when:

- V23 master prompt exists.
- V23 release candidate manifest exists.
- Release validation includes V23 artifacts.
- README links the release candidate manifest.
- Frontend smoke/typecheck/build still pass.
- Backend tests still pass.
- GitHub CI is green after push.

