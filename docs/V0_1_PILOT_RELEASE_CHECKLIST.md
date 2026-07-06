# v0.1 Pilot Release Checklist

ASTRA Clinic Core can be tagged as `v0.1-pilot` only after every item below is reviewed.

- [x] v0.1-pilot tag is blocked if any P0/P1 issue is open.
- [x] P2 issues that remain open are documented in release notes.
- [ ] P3 issues that remain open are accepted by the release maintainer.
- [ ] CI green.
- [x] Backend tests green.
- [x] Frontend typecheck green.
- [x] Frontend build green.
- [x] Pilot demo smoke green.
- [ ] Demo seed/reset verified.
- [x] Pilot runbook followed end-to-end.
- [x] No P0/P1 pilot issues open.
- [x] Real data readiness checklist reviewed and still blocks real patient data.
- [ ] Backup/restore docs reviewed.
- [x] Fiscalization marked noop/stub.
- [x] Demo banner visible.
- [x] `/api/public-config` confirms `real_data_allowed=false` for demo.
- [ ] API keys reviewed and deactivated after demo.

V17 readiness note:

- `docs/V0_1_TAG_READY.md` contains the evidence summary, tag command and rollback command.
- Remaining unchecked items require maintainer review before the tag command is run.

Release note:

- This release is for closed demo/pilot use only.
- Do not enter real patient data.
- Do not use for real Croatian fiscalization.
