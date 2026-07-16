# Phase D — Activity-specific preparation

`ActivityPreparationRequirement` stores the requirement, approved patient instruction, category, state, template provenance, review metadata, and owning activity.

The visit-level API groups identical canonical keys while preserving every activity and service name. A requirement is complete only when each applicable activity row is resolved. Medication, anticoagulant, antiplatelet, and diabetes review cannot be confirmed without the clinical-review permission.

Different instructions under the same canonical key are never merged by textual inference. They create a clinical blocker, set preparation to review-required, and remain visible as contradictory until a human resolves them.

