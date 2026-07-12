# ASTRA Gastroenterology Suite v1

Status: implemented on Clinical Module SDK 1.0, demo/pilot only.

The suite adds a specialty workspace at `/gastroenterology` and a validated data-only module package. It connects existing gastro appointments, reviewed and pending clinical documents, clinical episodes, workflow tasks, services, material templates, preparation instructions, and source-linked knowledge without duplicating Clinic Core objects.

The care rail follows the operational sequence: appointment, document review, episode context, next task. It is not a score, triage mechanism, diagnosis, treatment recommendation, or clearance decision.

The module manifest declares only services, material templates, workflows, and patient instructions. No executable code, migrations, remote hooks, autonomous AI, patient messaging, or real-data authorization is included.

Physicians remain responsible for clinical interpretation. Nurses and secretary/administrators may support operational tasks according to RBAC, but cannot confirm physician review or clinical decisions.
