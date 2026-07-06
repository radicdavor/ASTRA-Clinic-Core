# v0.1 Pilot Release Checklist

ASTRA Clinic Core can be tagged as `v0.1-pilot` only after every item below is reviewed.

- [x] v0.1-pilot tag is blocked if any P0/P1 issue is open.
- [x] P2 issues that remain open are documented in release notes.
- [ ] P3 issues that remain open are accepted by the release maintainer.
- [x] CI green.
- [x] Backend tests green.
- [x] Frontend typecheck green.
- [x] Frontend build green.
- [x] Pilot demo smoke green.
- [x] Demo seed/reset verified.
- [x] Pilot runbook followed end-to-end.
- [x] No P0/P1 pilot issues open.
- [x] Real data readiness checklist reviewed and still blocks real patient data.
- [x] Backup/restore docs reviewed.
- [x] Fiscalization marked noop/stub.
- [x] Demo banner visible.
- [x] `/api/public-config` confirms `real_data_allowed=false` for demo.
- [x] API keys reviewed and deactivated after demo.
- [x] V23 release candidate manifest reviewed before tag decision.

V18 readiness note:

- OIB is optional and remains demo/pilot-only until real-data readiness is approved.
- Appointment creation requires a resolved patient selected from search results.
- Contextual help has been added to key Novi/Dodaj/Spremi/Izdaj/Zaprimi workflows.

V17 readiness note:

- `docs/V0_1_TAG_READY.md` contains the evidence summary, tag command and rollback command.
- Remaining unchecked items require maintainer review before the tag command is run.

Release note:

- This release is for closed demo/pilot use only.
- Do not enter real patient data.
- Do not use for real Croatian fiscalization.
