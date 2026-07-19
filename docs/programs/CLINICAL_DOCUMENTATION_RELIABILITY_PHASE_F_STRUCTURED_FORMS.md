# Phase F - Structured endoscopy forms

Status: implemented for synthetic gastroenterology evaluation.

The form engine supports controlled repeatable structures for:

- repeatable groups
- structured polyp lists
- structured biopsy lists
- structured specimen lists
- structured intervention lists
- structured segment findings
- structured diagnosis lists
- structured product usage

Each repeatable item requires a stable `item_id`. Backend validation rejects unknown item fields, missing required item fields, duplicate item IDs, duplicate specimen labels, invalid enum values, invalid numeric values, and excessive item counts.

The published synthetic gastroscopy form captures indication, preparation, sedation, instrument, examination extent, esophageal/gastric/duodenal findings, biopsies, interventions, specimens, complications, diagnoses, recommendations, and follow-up.

The published synthetic colonoscopy form captures indication, bowel preparation, sedation, instrument, extent, terminal ileum, segment findings, polyps, interventions, biopsies, polypectomies, clips, withdrawal time, specimens, complications, diagnoses, recommendations, and follow-up.

The legacy generic `Status` field is not used as a substitute for structured endoscopy documentation.
