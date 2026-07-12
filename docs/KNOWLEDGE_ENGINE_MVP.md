# ASTRA Knowledge Engine MVP

Status: implemented, demo/pilot only.

Knowledge Engine manages versioned, source-linked clinical protocols. Every protocol begins as a draft and becomes official only after physician review. An official protocol requires an HTTPS source and at least one structured rule.

The engine deliberately does not match rules to patients, generate diagnoses, recommend treatment, assign clinical priority, or create workflow tasks. Rules are reference statements for human interpretation. Patient-specific reasoning, real AI providers, specialty automation, and real-data use remain deferred.

Routes: `/knowledge`, `/knowledge/{id}`.

API: `GET/POST /api/knowledge-protocols`, `GET /api/knowledge-protocols/{id}`, `POST /review`, `POST /archive`.

Permissions: `knowledge_protocols.read`, `knowledge_protocols.write`, `knowledge_protocols.review`.

All create, review, and archive actions are audited.
