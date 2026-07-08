# ASTRA Clinic Core

> Sigurnosna napomena: zadani korisnik, lozinka i lokalne Docker postavke su samo za razvoj. Prije stvarne uporabe promijenite admin lozinku, postavite jak `JWT_SECRET`, ogranicite CORS, koristite HTTPS, podesite backup PostgreSQL baze i napravite GDPR/access-control provjeru. ASTRA Clinic Core nije certificirani EMR i nije certificirani medicinski uredaj.

ASTRA Clinic Core je open-source modularna jezgra za rad klinike: naručivanje pacijenata, dnevni raspored, tijek pacijenta, API integracije, audit log, osnovni RBAC, inventar, nabava i priprema naplate.

Ovo nije puni EMR ni veliki ERP. MVP je namjerno fokusiran na operativni tijek klinike i modularnu arhitekturu za buduće medicinske module.

## Pilot status

Current stage: closed demo/pilot with demo data only.

- Do not enter real patient data.
- Real Croatian fiscalization is not implemented; current mode is noop/stub.
- Use demo seed/reset for pilot sessions:

```bash
docker compose exec backend python -m app.demo.seed
docker compose exec backend python -m app.demo.reset
```

Pilot documents:

- [ASTRA Architecture Bible](docs/ASTRA_ARCHITECTURE_BIBLE.md)
- [ASTRA Design System](docs/ASTRA_DESIGN_SYSTEM.md)
- [ASTRA Workspace Architecture](docs/ASTRA_WORKSPACE_ARCHITECTURE.md)
- [ASTRA Patient Clinical Knowledge Model](docs/ASTRA_PATIENT_CLINICAL_KNOWLEDGE_MODEL.md)
- [Patient Clinical Knowledge Layer MVP](docs/PATIENT_CLINICAL_KNOWLEDGE_LAYER_MVP.md)
- [Patient Clinical Summary MVP](docs/PATIENT_CLINICAL_SUMMARY_MVP.md)
- [Reception and Resource Scheduling](docs/RECEPTION_AND_RESOURCE_SCHEDULING.md)
- [Program 1 - ASTRA Clinical Workflow](docs/programs/PROGRAM_1_ASTRA_CLINICAL_WORKFLOW.md)
- [Program 1 Glossary](docs/programs/PROGRAM_1_GLOSSARY.md)
- [Program 1 Domain Object Mapping](docs/programs/PROGRAM_1_DOMAIN_OBJECT_MAPPING.md)
- [Program 1 Phase A - Patient Knowledge Stabilization Plan](docs/programs/PROGRAM_1_PHASE_A_PATIENT_KNOWLEDGE_STABILIZATION_PLAN.md)
- [Program 1 Review Pass 1 - Architectural Consistency Audit](docs/programs/PROGRAM_1_REVIEW_PASS_1_ARCHITECTURAL_CONSISTENCY_AUDIT.md)
- [ASTRA Readiness Model](docs/ASTRA_READINESS_MODEL.md)
- [ASTRA Operational Evidence Loop](docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md)
- [V20 Readiness Cockpit](docs/V20_READINESS_COCKPIT.md)
- [V23 Pilot Release Candidate](docs/V23_PILOT_RELEASE_CANDIDATE.md)
- [Codex Architecture Bible instructions](docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md)
- [V19 Architecture Bible compliance gate](docs/V19_ARCHITECTURE_BIBLE_COMPLIANCE_GATE.md)
- [Pilot runbook](docs/PILOT_RUNBOOK.md)
- [Program 1 Phase A hardening audit](docs/programs/PROGRAM_1_PHASE_A_HARDENING_AUDIT.md)
- [Program 1 Open Questions Contract](docs/programs/PROGRAM_1_OPEN_QUESTIONS_CONTRACT.md)
- [Program 1 ClinicalDocument Detail UX Contract](docs/programs/PROGRAM_1_CLINICAL_DOCUMENT_DETAIL_UX_CONTRACT.md)
- [Program 1 Clinical Evidence Timeline Contract](docs/programs/PROGRAM_1_CLINICAL_EVIDENCE_TIMELINE_CONTRACT.md)
- [Program 1 Phase A Regression Gate](docs/programs/PROGRAM_1_PHASE_A_REGRESSION_GATE.md)
- [Program 1 Phase A Regression Gate Runbook](docs/programs/PROGRAM_1_PHASE_A_REGRESSION_GATE_RUNBOOK.md)
- [Program 1 Phase A9 Core Route Modularization](docs/programs/PROGRAM_1_PHASE_A9_CORE_ROUTE_MODULARIZATION.md)
- [Program 1 Phase A10 Core Route Domain Split Plan](docs/programs/PROGRAM_1_PHASE_A10_CORE_ROUTE_DOMAIN_SPLIT_PLAN.md)
- [Program 1 Phase A11 regression notes](docs/programs/PROGRAM_1_PHASE_A11_REGRESSION_NOTES.md)
- [Program 1 Phase A12 regression notes](docs/programs/PROGRAM_1_PHASE_A12_REGRESSION_NOTES.md)
- [Program 1 Phase A13 regression notes](docs/programs/PROGRAM_1_PHASE_A13_REGRESSION_NOTES.md)
- [Program 1 Phase A14 regression notes](docs/programs/PROGRAM_1_PHASE_A14_REGRESSION_NOTES.md)
- [Program 1 Phase A15 regression notes](docs/programs/PROGRAM_1_PHASE_A15_REGRESSION_NOTES.md)
- [Program 1 Phase A16 Appointment and Reception Route Split](docs/programs/PROGRAM_1_PHASE_A16_APPOINTMENT_RECEPTION_ROUTE_SPLIT.md)
- [Program 1 Phase A16 regression notes](docs/programs/PROGRAM_1_PHASE_A16_REGRESSION_NOTES.md)
- [Program 1 Phase A17 Episode Route Split](docs/programs/PROGRAM_1_PHASE_A17_EPISODE_ROUTE_SPLIT.md)
- [Program 1 Phase A17 regression notes](docs/programs/PROGRAM_1_PHASE_A17_REGRESSION_NOTES.md)
- [Program 1 Phase A18 Catalog Search Audit Route Split](docs/programs/PROGRAM_1_PHASE_A18_CATALOG_SEARCH_AUDIT_ROUTE_SPLIT.md)
- [Program 1 Phase A18 regression notes](docs/programs/PROGRAM_1_PHASE_A18_REGRESSION_NOTES.md)
- [Program 1 Phase A closure report](docs/programs/PROGRAM_1_PHASE_A_CLOSURE_REPORT.md)
- [Program 1 Phase A Go/No-Go matrix](docs/programs/PROGRAM_1_PHASE_A_GO_NO_GO_MATRIX.md)
- [Program 1 Phase B decision brief](docs/programs/PROGRAM_1_PHASE_B_DECISION_BRIEF.md)
- [Program 1 Phase B0 Clinical Readiness Gate Operating Model](docs/programs/PROGRAM_1_PHASE_B0_CLINICAL_READINESS_GATE_OPERATING_MODEL.md)
- [Program 1 Phase B0 Clinical Readiness Roles](docs/programs/PROGRAM_1_PHASE_B0_CLINICAL_READINESS_ROLES.md)
- [Program 1 Phase B0 Clinical Readiness Specialty Examples](docs/programs/PROGRAM_1_PHASE_B0_CLINICAL_READINESS_SPECIALTY_EXAMPLES.md)
- [Program 1 Phase B0 Clinical Readiness Implementation Boundaries](docs/programs/PROGRAM_1_PHASE_B0_CLINICAL_READINESS_IMPLEMENTATION_BOUNDARIES.md)
- [Program 1 Phase B1 Clinical Readiness Vocabulary](docs/programs/PROGRAM_1_PHASE_B1_CLINICAL_READINESS_VOCABULARY.md)
- [Program 1 Phase B1 Clinical Readiness Domain Mapping](docs/programs/PROGRAM_1_PHASE_B1_CLINICAL_READINESS_DOMAIN_MAPPING.md)
- [Program 1 Phase B1 Clinical Readiness Status Taxonomy](docs/programs/PROGRAM_1_PHASE_B1_CLINICAL_READINESS_STATUS_TAXONOMY.md)
- [Program 1 Phase B1 Clinical Readiness Source Evidence Mapping](docs/programs/PROGRAM_1_PHASE_B1_CLINICAL_READINESS_SOURCE_EVIDENCE_MAPPING.md)
- [Program 1 Phase B2 Clinical Readiness API Contract](docs/programs/PROGRAM_1_PHASE_B2_CLINICAL_READINESS_API_CONTRACT.md)
- [Program 1 Phase B2 Clinical Readiness UI Contract](docs/programs/PROGRAM_1_PHASE_B2_CLINICAL_READINESS_UI_CONTRACT.md)
- [Program 1 Phase B2 Clinical Readiness Preview Data Contract](docs/programs/PROGRAM_1_PHASE_B2_CLINICAL_READINESS_PREVIEW_DATA_CONTRACT.md)
- [Program 1 Phase B2 Clinical Readiness Safety Regression Contract](docs/programs/PROGRAM_1_PHASE_B2_CLINICAL_READINESS_SAFETY_REGRESSION_CONTRACT.md)
- [Program 1 Phase B3 regression notes](docs/programs/PROGRAM_1_PHASE_B3_REGRESSION_NOTES.md)
- [Program 1 Phase B4 Clinical Readiness Template Design](docs/programs/PROGRAM_1_PHASE_B4_CLINICAL_READINESS_TEMPLATE_DESIGN.md)
- [Program 1 Phase B4 regression notes](docs/programs/PROGRAM_1_PHASE_B4_REGRESSION_NOTES.md)
- [Program 1 Phase B5 Clinical Readiness Template Binding Design](docs/programs/PROGRAM_1_PHASE_B5_CLINICAL_READINESS_TEMPLATE_BINDING_DESIGN.md)
- [Program 1 Phase B5 Clinical Readiness Template Governance](docs/programs/PROGRAM_1_PHASE_B5_CLINICAL_READINESS_TEMPLATE_GOVERNANCE.md)
- [Program 1 Phase B5 regression notes](docs/programs/PROGRAM_1_PHASE_B5_REGRESSION_NOTES.md)
- [Program 1 Phase B6 Explicit Service Binding Prototype](docs/programs/PROGRAM_1_PHASE_B6_EXPLICIT_SERVICE_BINDING_PROTOTYPE.md)
- [Program 1 Phase B6 regression notes](docs/programs/PROGRAM_1_PHASE_B6_REGRESSION_NOTES.md)
- [Program 1 Phase B7 Clinical Readiness Template Versioning Design](docs/programs/PROGRAM_1_PHASE_B7_CLINICAL_READINESS_TEMPLATE_VERSIONING_DESIGN.md)
- [Program 1 Phase B7 regression notes](docs/programs/PROGRAM_1_PHASE_B7_REGRESSION_NOTES.md)
- [Program 1 Phase B8 Clinical Readiness Snapshot Design](docs/programs/PROGRAM_1_PHASE_B8_CLINICAL_READINESS_SNAPSHOT_DESIGN.md)
- [Program 1 Phase B8 Clinical Readiness Snapshot Boundaries](docs/programs/PROGRAM_1_PHASE_B8_CLINICAL_READINESS_SNAPSHOT_BOUNDARIES.md)
- [Program 1 Phase B8 regression notes](docs/programs/PROGRAM_1_PHASE_B8_REGRESSION_NOTES.md)
- [Program 1 Phase B9 Clinical Readiness Snapshot Persistence Model](docs/programs/PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_PERSISTENCE_MODEL.md)
- [Program 1 Phase B9 Clinical Readiness Snapshot Audit Model](docs/programs/PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_AUDIT_MODEL.md)
- [Program 1 Phase B9 Clinical Readiness Snapshot Lifecycle Governance](docs/programs/PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_LIFECYCLE_GOVERNANCE.md)
- [Program 1 Phase B9 Clinical Readiness Snapshot Regression Gate](docs/programs/PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_REGRESSION_GATE.md)
- [Program 1 Phase B9 regression notes](docs/programs/PROGRAM_1_PHASE_B9_REGRESSION_NOTES.md)
- [Program 1 Phase B10 Snapshot Persistence Migration Review](docs/programs/PROGRAM_1_PHASE_B10_SNAPSHOT_PERSISTENCE_MIGRATION_REVIEW.md)
- [Program 1 Phase B11 Snapshot Capture Endpoint Design](docs/programs/PROGRAM_1_PHASE_B11_SNAPSHOT_CAPTURE_ENDPOINT_DESIGN.md)
- [Program 1 Phase B12 Snapshot Permission Contract](docs/programs/PROGRAM_1_PHASE_B12_SNAPSHOT_PERMISSION_CONTRACT.md)
- [Program 1 Phase B12 Snapshot Audit Payload Contract](docs/programs/PROGRAM_1_PHASE_B12_SNAPSHOT_AUDIT_PAYLOAD_CONTRACT.md)
- [Program 1 Phase B12 Snapshot Permission/Audit No-Go Matrix](docs/programs/PROGRAM_1_PHASE_B12_SNAPSHOT_PERMISSION_AUDIT_NO_GO_MATRIX.md)
- [Program 1 Phase B12 Snapshot Implementation Gate](docs/programs/PROGRAM_1_PHASE_B12_SNAPSHOT_IMPLEMENTATION_GATE.md)
- [Program 1 Phase B12 regression notes](docs/programs/PROGRAM_1_PHASE_B12_REGRESSION_NOTES.md)
- [Program 1 Phase B13 regression notes](docs/programs/PROGRAM_1_PHASE_B13_REGRESSION_NOTES.md)
- [Program 1 Phase B14 regression notes](docs/programs/PROGRAM_1_PHASE_B14_REGRESSION_NOTES.md)
- [Program 1 Phase B15 regression notes](docs/programs/PROGRAM_1_PHASE_B15_REGRESSION_NOTES.md)
- [Program 1 Phase B16 regression notes](docs/programs/PROGRAM_1_PHASE_B16_REGRESSION_NOTES.md)
- [Program 1 Phase B17 regression notes](docs/programs/PROGRAM_1_PHASE_B17_REGRESSION_NOTES.md)
- [Program 1 Phase B18 regression notes](docs/programs/PROGRAM_1_PHASE_B18_REGRESSION_NOTES.md)
- [Program 1 Phase B19 regression notes](docs/programs/PROGRAM_1_PHASE_B19_REGRESSION_NOTES.md)
- [Program 1 Phase B20 regression notes](docs/programs/PROGRAM_1_PHASE_B20_REGRESSION_NOTES.md)
- [Program 1 Phase B21 Snapshot Canonical Disclaimer and Immutability](docs/programs/PROGRAM_1_PHASE_B21_SNAPSHOT_CANONICAL_DISCLAIMER_AND_IMMUTABILITY.md)
- [Program 1 Phase B21 regression notes](docs/programs/PROGRAM_1_PHASE_B21_REGRESSION_NOTES.md)
- [Program 1 Phase B22 Snapshot Supersession Contract](docs/programs/PROGRAM_1_PHASE_B22_SNAPSHOT_SUPERSESSION_CONTRACT.md)
- [Program 1 Phase B22 Snapshot Supersession Audit Contract](docs/programs/PROGRAM_1_PHASE_B22_SNAPSHOT_SUPERSESSION_AUDIT_CONTRACT.md)
- [Program 1 Phase B22 Snapshot Supersession No-Go Matrix](docs/programs/PROGRAM_1_PHASE_B22_SNAPSHOT_SUPERSESSION_NO_GO_MATRIX.md)
- [Program 1 Phase B22 regression notes](docs/programs/PROGRAM_1_PHASE_B22_REGRESSION_NOTES.md)
- [Program 1 Phase B23 regression notes](docs/programs/PROGRAM_1_PHASE_B23_REGRESSION_NOTES.md)
- [Program 1 Phase B24 regression notes](docs/programs/PROGRAM_1_PHASE_B24_REGRESSION_NOTES.md)
- [Program 1 Phase B25 regression notes](docs/programs/PROGRAM_1_PHASE_B25_REGRESSION_NOTES.md)
- [Program 1 Phase B26 Snapshot Governance Stabilization](docs/programs/PROGRAM_1_PHASE_B26_SNAPSHOT_GOVERNANCE_STABILIZATION.md)
- [Program 1 Phase B26 regression notes](docs/programs/PROGRAM_1_PHASE_B26_REGRESSION_NOTES.md)
- [Program 1 Phase B27 regression notes](docs/programs/PROGRAM_1_PHASE_B27_REGRESSION_NOTES.md)
- [Program 1 Phase B Snapshot Closure Report](docs/programs/PROGRAM_1_PHASE_B_SNAPSHOT_CLOSURE_REPORT.md)
- [Program 1 Phase B Snapshot Go/No-Go Matrix](docs/programs/PROGRAM_1_PHASE_B_SNAPSHOT_GO_NO_GO_MATRIX.md)
- [Program 1 Phase B Snapshot Next-Step Decision Brief](docs/programs/PROGRAM_1_PHASE_B_SNAPSHOT_NEXT_STEP_DECISION_BRIEF.md)
- [Program 1 Phase B28 regression notes](docs/programs/PROGRAM_1_PHASE_B28_REGRESSION_NOTES.md)
- [Program 1 Phase B29 Snapshot Production Risk Hardening](docs/programs/PROGRAM_1_PHASE_B29_SNAPSHOT_PRODUCTION_RISK_HARDENING.md)
- [Program 1 Phase B29 DB Immutability Trigger Design](docs/programs/PROGRAM_1_PHASE_B29_DB_IMMUTABILITY_TRIGGER_DESIGN.md)
- [Program 1 Phase B29 regression notes](docs/programs/PROGRAM_1_PHASE_B29_REGRESSION_NOTES.md)
- [Program 1 Phase B30 Snapshot DB Immutability Trigger Prototype](docs/programs/PROGRAM_1_PHASE_B30_SNAPSHOT_DB_IMMUTABILITY_TRIGGER_PROTOTYPE.md)
- [Program 1 Phase B30 regression notes](docs/programs/PROGRAM_1_PHASE_B30_REGRESSION_NOTES.md)
- [Program 1 Phase B31 Snapshot Audit Review and Retention Runbook](docs/programs/PROGRAM_1_PHASE_B31_SNAPSHOT_AUDIT_REVIEW_AND_RETENTION_RUNBOOK.md)
- [Program 1 Phase B31 regression notes](docs/programs/PROGRAM_1_PHASE_B31_REGRESSION_NOTES.md)
- [Program 1 Phase B32 regression notes](docs/programs/PROGRAM_1_PHASE_B32_REGRESSION_NOTES.md)
- [Program 1 Phase B33 Snapshot Audit Export Contract](docs/programs/PROGRAM_1_PHASE_B33_SNAPSHOT_AUDIT_EXPORT_CONTRACT.md)
- [Program 1 Phase B33 regression notes](docs/programs/PROGRAM_1_PHASE_B33_REGRESSION_NOTES.md)
- [Program 1 Phase B34 Snapshot Backup Restore Consistency Runbook](docs/programs/PROGRAM_1_PHASE_B34_SNAPSHOT_BACKUP_RESTORE_CONSISTENCY_RUNBOOK.md)
- [Program 1 Phase B34 regression notes](docs/programs/PROGRAM_1_PHASE_B34_REGRESSION_NOTES.md)
- [Program 1 Phase B35 regression notes](docs/programs/PROGRAM_1_PHASE_B35_REGRESSION_NOTES.md)
- [Program 1 Phase B36 regression notes](docs/programs/PROGRAM_1_PHASE_B36_REGRESSION_NOTES.md)
- [Program 1 Phase B37 Snapshot CI Gate](docs/programs/PROGRAM_1_PHASE_B37_SNAPSHOT_CI_GATE.md)
- [Program 1 Phase B37 regression notes](docs/programs/PROGRAM_1_PHASE_B37_REGRESSION_NOTES.md)
- [Program 1 Phase B38 Snapshot Disclaimer Review](docs/programs/PROGRAM_1_PHASE_B38_SNAPSHOT_DISCLAIMER_REVIEW.md)
- [Program 1 Phase B38 regression notes](docs/programs/PROGRAM_1_PHASE_B38_REGRESSION_NOTES.md)
- [Program 1 Phase B39 Snapshot Real-Data No-Go Checklist](docs/programs/PROGRAM_1_PHASE_B39_SNAPSHOT_REAL_DATA_NO_GO_CHECKLIST.md)
- [Program 1 Phase B39 regression notes](docs/programs/PROGRAM_1_PHASE_B39_REGRESSION_NOTES.md)
- [Program 1 Phase B40 Snapshot Production Governance Closure Matrix](docs/programs/PROGRAM_1_PHASE_B40_SNAPSHOT_PRODUCTION_GOVERNANCE_CLOSURE_MATRIX.md)
- [Program 1 Phase B40 regression notes](docs/programs/PROGRAM_1_PHASE_B40_REGRESSION_NOTES.md)
- [Program 1 Phase B31-B41 Snapshot Hardening Closure Report](docs/programs/PROGRAM_1_PHASE_B31_B41_SNAPSHOT_HARDENING_CLOSURE_REPORT.md)
- [Program 1 Phase B41 regression notes](docs/programs/PROGRAM_1_PHASE_B41_REGRESSION_NOTES.md)
- [Program 1 Phase C0 Clinical Readiness Enforcement Readiness Design](docs/programs/PROGRAM_1_PHASE_C0_CLINICAL_READINESS_ENFORCEMENT_READINESS_DESIGN.md)
- [Program 1 Phase C0 regression notes](docs/programs/PROGRAM_1_PHASE_C0_REGRESSION_NOTES.md)
- [Program 1 Phase C1 Enforcement Vocabulary and Forbidden Semantics](docs/programs/PROGRAM_1_PHASE_C1_ENFORCEMENT_VOCABULARY_AND_FORBIDDEN_SEMANTICS.md)
- [Program 1 Phase C1 regression notes](docs/programs/PROGRAM_1_PHASE_C1_REGRESSION_NOTES.md)
- [Program 1 Phase C2 Human Responsibility Model](docs/programs/PROGRAM_1_PHASE_C2_HUMAN_RESPONSIBILITY_MODEL.md)
- [Program 1 Phase C3 Enforcement Risk Register](docs/programs/PROGRAM_1_PHASE_C3_ENFORCEMENT_RISK_REGISTER.md)
- [Program 1 Phase C4 Enforcement No-Go Matrix](docs/programs/PROGRAM_1_PHASE_C4_ENFORCEMENT_NO_GO_MATRIX.md)
- [Program 1 Phase C5 Advisory Signal Contract](docs/programs/PROGRAM_1_PHASE_C5_ADVISORY_SIGNAL_CONTRACT.md)
- [Program 1 Phase C6 regression notes](docs/programs/PROGRAM_1_PHASE_C6_REGRESSION_NOTES.md)
- [Program 1 Phase C7 Advisory Signal Preview Mapping](docs/programs/PROGRAM_1_PHASE_C7_ADVISORY_SIGNAL_PREVIEW_MAPPING.md)
- [Program 1 Phase C8 regression notes](docs/programs/PROGRAM_1_PHASE_C8_REGRESSION_NOTES.md)
- [Program 1 Phase C9 Enforcement Permission Model Design](docs/programs/PROGRAM_1_PHASE_C9_ENFORCEMENT_PERMISSION_MODEL_DESIGN.md)
- [Program 1 Phase C10 Review Acknowledgment Design](docs/programs/PROGRAM_1_PHASE_C10_REVIEW_ACKNOWLEDGMENT_DESIGN.md)
- [Program 1 Phase C11 Enforcement Audit Contract](docs/programs/PROGRAM_1_PHASE_C11_ENFORCEMENT_AUDIT_CONTRACT.md)
- [Program 1 Phase C12 Enforcement UI Copy and Safety Labels](docs/programs/PROGRAM_1_PHASE_C12_ENFORCEMENT_UI_COPY_AND_SAFETY_LABELS.md)
- [Program 1 Phase C13 Enforcement Readiness CI Gate](docs/programs/PROGRAM_1_PHASE_C13_ENFORCEMENT_READINESS_CI_GATE.md)
- [Program 1 Phase C14 Enforcement Readiness Go/No-Go Matrix](docs/programs/PROGRAM_1_PHASE_C14_ENFORCEMENT_READINESS_GO_NO_GO_MATRIX.md)
- [Program 1 Phase C0-C15 Enforcement Readiness Closure Report](docs/programs/PROGRAM_1_PHASE_C0_C15_ENFORCEMENT_READINESS_CLOSURE_REPORT.md)
- [Program 1 Phase C15 Next-Step Decision Brief](docs/programs/PROGRAM_1_PHASE_C15_NEXT_STEP_DECISION_BRIEF.md)
- [Program 1 Phase C15 regression notes](docs/programs/PROGRAM_1_PHASE_C15_REGRESSION_NOTES.md)
- [Program 1 Phase C16 Human Review Acknowledgment Contract](docs/programs/PROGRAM_1_PHASE_C16_HUMAN_REVIEW_ACKNOWLEDGMENT_CONTRACT.md)
- [Program 1 Phase C16 regression notes](docs/programs/PROGRAM_1_PHASE_C16_REGRESSION_NOTES.md)
- [Program 1 Phase C17 Acknowledgment Forbidden Semantics Matrix](docs/programs/PROGRAM_1_PHASE_C17_ACKNOWLEDGMENT_FORBIDDEN_SEMANTICS_MATRIX.md)
- [Program 1 Phase C17 regression notes](docs/programs/PROGRAM_1_PHASE_C17_REGRESSION_NOTES.md)
- [Program 1 Phase C18 Acknowledgment Audit Payload Contract](docs/programs/PROGRAM_1_PHASE_C18_ACKNOWLEDGMENT_AUDIT_PAYLOAD_CONTRACT.md)
- [Program 1 Phase C19 regression notes](docs/programs/PROGRAM_1_PHASE_C19_REGRESSION_NOTES.md)
- [Program 1 Phase C20 regression notes](docs/programs/PROGRAM_1_PHASE_C20_REGRESSION_NOTES.md)
- [Program 1 Phase C21 Advisory Read-Only UI Surface Design](docs/programs/PROGRAM_1_PHASE_C21_ADVISORY_READ_ONLY_UI_SURFACE_DESIGN.md)
- [Program 1 Phase C22 regression notes](docs/programs/PROGRAM_1_PHASE_C22_REGRESSION_NOTES.md)
- [Program 1 Phase C23 regression notes](docs/programs/PROGRAM_1_PHASE_C23_REGRESSION_NOTES.md)
- [Program 1 Phase C24 Human Review Acknowledgment Go/No-Go Matrix](docs/programs/PROGRAM_1_PHASE_C24_HUMAN_REVIEW_ACKNOWLEDGMENT_GO_NO_GO_MATRIX.md)
- [Program 1 Phase C25 Acknowledgment Advisory CI Gate](docs/programs/PROGRAM_1_PHASE_C25_ACKNOWLEDGMENT_ADVISORY_CI_GATE.md)
- [Program 1 Phase C26 Closure Report](docs/programs/PROGRAM_1_PHASE_C26_CLOSURE_REPORT.md)
- [Program 1 Phase C26 Next-Step Decision Brief](docs/programs/PROGRAM_1_PHASE_C26_NEXT_STEP_DECISION_BRIEF.md)
- [Program 1 Phase C26 regression notes](docs/programs/PROGRAM_1_PHASE_C26_REGRESSION_NOTES.md)
- [Program 1 Phase C27 Acknowledgment Persistence Design](docs/programs/PROGRAM_1_PHASE_C27_ACKNOWLEDGMENT_PERSISTENCE_DESIGN.md)
- [Program 1 Phase C27 regression notes](docs/programs/PROGRAM_1_PHASE_C27_REGRESSION_NOTES.md)
- [Program 1 Phase C28 Acknowledgment Persistence No-Go Matrix](docs/programs/PROGRAM_1_PHASE_C28_ACKNOWLEDGMENT_PERSISTENCE_NO_GO_MATRIX.md)
- [Program 1 Phase C28 regression notes](docs/programs/PROGRAM_1_PHASE_C28_REGRESSION_NOTES.md)
- [Program 1 Phase C29 Acknowledgment Migration Review](docs/programs/PROGRAM_1_PHASE_C29_ACKNOWLEDGMENT_MIGRATION_REVIEW.md)
- [Program 1 Phase C29 regression notes](docs/programs/PROGRAM_1_PHASE_C29_REGRESSION_NOTES.md)
- [Program 1 Phase C30 Acknowledgment Permission Governance](docs/programs/PROGRAM_1_PHASE_C30_ACKNOWLEDGMENT_PERMISSION_GOVERNANCE.md)
- [Program 1 Phase C30 regression notes](docs/programs/PROGRAM_1_PHASE_C30_REGRESSION_NOTES.md)
- [Program 1 Phase C31 Acknowledgment Audit Governance](docs/programs/PROGRAM_1_PHASE_C31_ACKNOWLEDGMENT_AUDIT_GOVERNANCE.md)
- [Program 1 Phase C31 regression notes](docs/programs/PROGRAM_1_PHASE_C31_REGRESSION_NOTES.md)
- [Program 1 Phase C32 Acknowledgment Retention and Rollback Rules](docs/programs/PROGRAM_1_PHASE_C32_ACKNOWLEDGMENT_RETENTION_AND_ROLLBACK_RULES.md)
- [Program 1 Phase C32 regression notes](docs/programs/PROGRAM_1_PHASE_C32_REGRESSION_NOTES.md)
- [Program 1 Phase C33 Runtime No-Go Regression Guard](docs/programs/PROGRAM_1_PHASE_C33_RUNTIME_NO_GO_REGRESSION_GUARD.md)
- [Program 1 Phase C33 regression notes](docs/programs/PROGRAM_1_PHASE_C33_REGRESSION_NOTES.md)
- [Program 1 Phase C34 Permission Seed No-Go Hardening](docs/programs/PROGRAM_1_PHASE_C34_PERMISSION_SEED_NO_GO_HARDENING.md)
- [Program 1 Phase C34 regression notes](docs/programs/PROGRAM_1_PHASE_C34_REGRESSION_NOTES.md)
- [Program 1 Phase C35 Acknowledgment UI Action No-Go Hardening](docs/programs/PROGRAM_1_PHASE_C35_ACKNOWLEDGMENT_UI_ACTION_NO_GO_HARDENING.md)
- [Program 1 Phase C35 regression notes](docs/programs/PROGRAM_1_PHASE_C35_REGRESSION_NOTES.md)
- [Program 1 Phase C36 Acknowledgment Persistence CI Gate](docs/programs/PROGRAM_1_PHASE_C36_ACKNOWLEDGMENT_PERSISTENCE_CI_GATE.md)
- [Program 1 Phase C36 regression notes](docs/programs/PROGRAM_1_PHASE_C36_REGRESSION_NOTES.md)
- [Program 1 Phase C37 Acknowledgment Persistence Closure Report](docs/programs/PROGRAM_1_PHASE_C37_ACKNOWLEDGMENT_PERSISTENCE_CLOSURE_REPORT.md)
- [Program 1 Phase C37 Go/No-Go Matrix](docs/programs/PROGRAM_1_PHASE_C37_GO_NO_GO_MATRIX.md)
- [Program 1 Phase C37 Next-Step Decision Brief](docs/programs/PROGRAM_1_PHASE_C37_NEXT_STEP_DECISION_BRIEF.md)
- [Program 1 Phase C37 regression notes](docs/programs/PROGRAM_1_PHASE_C37_REGRESSION_NOTES.md)
- [Program 1 Phase C38 Acknowledgment Endpoint Contract Design](docs/programs/PROGRAM_1_PHASE_C38_ACKNOWLEDGMENT_ENDPOINT_CONTRACT_DESIGN.md)
- [Program 1 Phase C38 regression notes](docs/programs/PROGRAM_1_PHASE_C38_REGRESSION_NOTES.md)
- [Program 1 Phase C39 Acknowledgment Request Response Contract](docs/programs/PROGRAM_1_PHASE_C39_ACKNOWLEDGMENT_REQUEST_RESPONSE_CONTRACT.md)
- [Program 1 Phase C39 regression notes](docs/programs/PROGRAM_1_PHASE_C39_REGRESSION_NOTES.md)
- [Program 1 Phase C40 Acknowledgment Error States Contract](docs/programs/PROGRAM_1_PHASE_C40_ACKNOWLEDGMENT_ERROR_STATES_CONTRACT.md)
- [Program 1 Phase C40 regression notes](docs/programs/PROGRAM_1_PHASE_C40_REGRESSION_NOTES.md)
- [Program 1 Phase C41 Acknowledgment Permission Boundary](docs/programs/PROGRAM_1_PHASE_C41_ACKNOWLEDGMENT_PERMISSION_BOUNDARY.md)
- [Program 1 Phase C41 regression notes](docs/programs/PROGRAM_1_PHASE_C41_REGRESSION_NOTES.md)
- [Program 1 Phase C42 Acknowledgment Audit Expectations](docs/programs/PROGRAM_1_PHASE_C42_ACKNOWLEDGMENT_AUDIT_EXPECTATIONS.md)
- [Program 1 Phase C42 regression notes](docs/programs/PROGRAM_1_PHASE_C42_REGRESSION_NOTES.md)
- [Program 1 Phase C43 Acknowledgment Idempotency Retry Policy](docs/programs/PROGRAM_1_PHASE_C43_ACKNOWLEDGMENT_IDEMPOTENCY_RETRY_POLICY.md)
- [Program 1 Phase C43 regression notes](docs/programs/PROGRAM_1_PHASE_C43_REGRESSION_NOTES.md)
- [Program 1 Phase C44 Acknowledgment Runtime No-Go Boundary](docs/programs/PROGRAM_1_PHASE_C44_ACKNOWLEDGMENT_RUNTIME_NO_GO_BOUNDARY.md)
- [Program 1 Phase C44 regression notes](docs/programs/PROGRAM_1_PHASE_C44_REGRESSION_NOTES.md)
- [Program 1 Phase C45 Endpoint Absence Regression Guard](docs/programs/PROGRAM_1_PHASE_C45_ENDPOINT_ABSENCE_REGRESSION_GUARD.md)
- [Program 1 Phase C45 regression notes](docs/programs/PROGRAM_1_PHASE_C45_REGRESSION_NOTES.md)
- [Program 1 Phase C46 Acknowledgment Endpoint CI Gate](docs/programs/PROGRAM_1_PHASE_C46_ACKNOWLEDGMENT_ENDPOINT_CI_GATE.md)
- [Program 1 Phase C46 regression notes](docs/programs/PROGRAM_1_PHASE_C46_REGRESSION_NOTES.md)
- [Program 1 Phase C47 Acknowledgment Endpoint Go/No-Go Matrix](docs/programs/PROGRAM_1_PHASE_C47_ACKNOWLEDGMENT_ENDPOINT_GO_NO_GO_MATRIX.md)
- [Program 1 Phase C48 Acknowledgment Endpoint Closure Report](docs/programs/PROGRAM_1_PHASE_C48_ACKNOWLEDGMENT_ENDPOINT_CLOSURE_REPORT.md)
- [Program 1 Phase C48 Next-Step Decision Brief](docs/programs/PROGRAM_1_PHASE_C48_NEXT_STEP_DECISION_BRIEF.md)
- [Program 1 Phase C48 regression notes](docs/programs/PROGRAM_1_PHASE_C48_REGRESSION_NOTES.md)
- [Lokalni LAN pristup](docs/LAN_ACCESS.md)
- [Program 1 audit event naming](docs/programs/PROGRAM_1_AUDIT_EVENT_NAMING.md)
- [Program 1 Phase A regression notes](docs/programs/PROGRAM_1_PHASE_A_REGRESSION_NOTES.md)
- [Program 1 Phase A5 regression notes](docs/programs/PROGRAM_1_PHASE_A5_REGRESSION_NOTES.md)
- [Program 1 Phase A6 regression notes](docs/programs/PROGRAM_1_PHASE_A6_REGRESSION_NOTES.md)
- [Program 1 Phase A7 regression notes](docs/programs/PROGRAM_1_PHASE_A7_REGRESSION_NOTES.md)
- [Program 1 Phase A8 regression notes](docs/programs/PROGRAM_1_PHASE_A8_REGRESSION_NOTES.md)
- [Program 1 Phase A9 regression notes](docs/programs/PROGRAM_1_PHASE_A9_REGRESSION_NOTES.md)
- [Real data readiness checklist](docs/REAL_DATA_READINESS_CHECKLIST.md)
- [v0.1 pilot release checklist](docs/V0_1_PILOT_RELEASE_CHECKLIST.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)

## Tehnologije

- Backend: Python FastAPI
- Baza: PostgreSQL
- ORM: SQLAlchemy 2.x
- Migracije: Alembic
- Frontend: React, TypeScript, Vite
- Auth: JWT prijava
- Deployment: Docker Compose

## Lokalno pokretanje

1. Kopirajte primjer okoline:

```bash
cp .env.example .env
```

2. Pokrenite sustav:

```bash
docker compose up --build
```

Backend Docker entrypoint automatski pokreće:

```bash
alembic upgrade head
python -m app.seed
```

Ako ste ranije pokretali prvu MVP verziju koja je bazu stvarala preko `create_all()`, resetirajte lokalni razvojni volume prije novog starta:

```bash
docker compose down -v
docker compose up --build
```

3. Otvorite:

- Aplikacija: http://localhost:5173
- API dokumentacija: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Za pristup s drugog uredaja u istoj mrezi otvorite:

- Aplikacija: `http://IP-ADRESA-RACUNALA:5173`
- API: `http://IP-ADRESA-RACUNALA:8000`

Frontend po defaultu koristi isti hostname na kojem je otvoren u browseru i port `8000`, pa `localhost` nije potreban za mrezni pristup.
Detalji su u [LAN uputi](docs/LAN_ACCESS.md).

Početna prijava:

- E-pošta: `admin@astra.local`
- Lozinka: `astra123`

## Testovi i CI

Lokalno pokretanje provjera:

```bash
make test
```

Backend testovi koriste izoliranu testnu bazu i ne ovise o ručnom seedanju razvojne baze. GitHub Actions CI se pokreće na svaki push i pull request, pokreće migracije nad testnim PostgreSQL-om, backend pytest suite, frontend typecheck i frontend production build.

PostgreSQL integration testovi koriste `TEST_DATABASE_URL`. Lokalno se preskaču ako ta varijabla nije postavljena; u CI-ju je postavljena na testni PostgreSQL servis.

Za produkciju postavite `APP_ENV=production`, jak `JWT_SECRET`, kraći `ACCESS_TOKEN_MINUTES` i eksplicitni `CORS_ORIGINS`. Aplikacija namjerno odbija startup u produkciji ako su JWT ili CORS postavke nesigurne.

## Što je uključeno

- Pacijenti: unos, popis, detalj i ažuriranje preko API-ja
- Termini: unos, popis, dnevni raspored, brza promjena statusa
- Alembic migracije umjesto startup `create_all()`
- Permission-based RBAC s eksplicitnim dozvolama po ulozi
- Strukturirani audit log s before/after JSON snapshotima i request ID-jem
- Validacija konflikta termina za liječnika i sobu
- Scoped API key autentikacija za AI agente preko `X-ASTRA-API-Key`
- Pretraživanje po pacijentu, usluzi i statusu
- Katalog usluga i modularni registar
- JWT prijava i osnovna kontrola uloga
