# Phase B — Controlled registries

Canonical clinical keys are owned by `backend/app/core/clinical_registries.py` and mirrored for interactive frontend controls in `frontend/src/constants/clinicalRegistries.ts`.

The controlled sets cover specialty, activity kind, intervention type, specimen type, retrieval status, pathology state, signed-report document type, clinical-form field type, preparation key, and pathology communication disposition. API schemas reject unknown new keys; database strings remain migration-safe for historical rows.

Free-text remains allowed only for clinical narrative, anatomical descriptions, notes, and human explanations. It is not accepted as a replacement for a controlled workflow key.

