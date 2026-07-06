# Known Limitations

ASTRA Clinic Core is currently a closed demo/pilot system for demo data only.

- Not production ready.
- No real patient data is allowed.
- OIB is supported only as an optional demo/pilot identifier until real-data readiness is formally approved.
- OIB checksum validation is not implemented yet; pilot validation checks only the 11-digit shape.
- Possible duplicate detection is a safety prompt, not a guaranteed master-patient-index match.
- No real Croatian fiscalization is implemented.
- Frontend e2e coverage is limited.
- Module loader is basic and data-only.
- Dedicated Invoice Workspace, Inventory Item Workspace and Purchase Order Workspace are still future work; V20 implements Patient Workspace first.
- Readiness cockpit supports pilot review only; it is not compliance certification and does not replace human pilot evidence.
- OpenEMR integration is not implemented.
- Google Calendar integration is not implemented.
- No full EMR charting.
- Clinical Episode is structural context only; it is not a diagnosis, care guideline or treatment plan engine.
- No clinical decision support.
- Clinical document extraction is a placeholder and must be physician-reviewed before it becomes official patient knowledge.
- OCR is not implemented; uploaded document text is manual/placeholder input.
- Patient Clinical Summary is source-linked and rule-based; it is not a diagnostic engine.
- No Workflow Engine.
- No Knowledge Engine.
- No AI automation.
- No prescription system.
- Not a certified EMR.
- Not a certified medical device.

These limitations must be reviewed before any real-data or production planning.
