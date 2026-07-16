# Phase G — Interventions, specimens, and pathology

Interventions use controlled types and structured site, technique, device, size, count, retrieval, and complication fields. Biopsy and retrieved-polypectomy interventions may create labelled pathology specimens.

Pathology creation is activity-scoped and idempotent. Specimens retain their source intervention, anatomical site, type, container, fixation, and collection time. A specimen cannot reference an intervention from another activity.

Clinical entry uses application controls and modals; browser prompts are removed. Signed reports preserve the structured snapshot rather than re-reading mutable intervention rows.

