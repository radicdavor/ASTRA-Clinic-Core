# Phase E — Repeatable structured form components

The form engine supports controlled repeatable groups for diagnoses, medication, anatomical sites, polyps, biopsies, interventions, specimens, and segment findings.

Every item has a stable `item_id`. Server validation enforces known item fields, required item values, maximum counts, unique item IDs, and unique specimen labels. Nested executable or arbitrary field types are rejected. Rendering is deterministic and excludes internal item IDs.

The React editor supports structured text, number, date, time, select, checkbox, and narrative fields. Adding and removing items is explicit and keyboard-accessible.

