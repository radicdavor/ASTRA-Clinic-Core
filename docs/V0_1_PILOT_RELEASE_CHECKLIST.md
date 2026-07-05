# v0.1 Pilot Release Checklist

ASTRA Clinic Core can be tagged as `v0.1-pilot` only after every item below is reviewed.

- [ ] v0.1-pilot tag is blocked if any P0/P1 issue is open.
- [ ] P2 issues that remain open are documented in release notes.
- [ ] P3 issues that remain open are accepted by the release maintainer.
- [ ] CI green.
- [ ] Backend tests green.
- [ ] Frontend typecheck green.
- [ ] Frontend build green.
- [ ] Pilot demo smoke green.
- [ ] Demo seed/reset verified.
- [ ] Pilot runbook followed end-to-end.
- [ ] No P0/P1 pilot issues open.
- [ ] Real data readiness checklist reviewed and still blocks real patient data.
- [ ] Backup/restore docs reviewed.
- [ ] Fiscalization marked noop/stub.
- [ ] Demo banner visible.
- [ ] `/api/public-config` confirms `real_data_allowed=false` for demo.
- [ ] API keys reviewed and deactivated after demo.

Release note:

- This release is for closed demo/pilot use only.
- Do not enter real patient data.
- Do not use for real Croatian fiscalization.
