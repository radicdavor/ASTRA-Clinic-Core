from __future__ import annotations

import ast
from pathlib import Path

import pytest


BACKEND = Path(__file__).resolve().parents[1]
SOURCE_PATHS = {
    "dependencies": BACKEND / "app/auth/dependencies.py",
    "patients": BACKEND / "app/api/routes/patients.py",
    "search": BACKEND / "app/api/routes/search.py",
    "appointments": BACKEND / "app/api/routes/appointments.py",
    "catalog_governance": BACKEND / "app/api/routes/catalog_governance.py",
    "intake": BACKEND / "app/api/routes/intake.py",
    "ai": BACKEND / "app/api/routes/ai.py",
    "reconciliation": BACKEND / "app/services/patient_identity_reconciliation.py",
    "reconciliation_routes": BACKEND / "app/api/routes/patient_identity_reconciliation.py",
    "reconciliation_model": BACKEND / "app/models/domain.py",
    "reconciliation_migration": BACKEND / "alembic/versions/0072_patient_identity_reconciliation.py",
}


def load_sources() -> dict[str, str]:
    return {name: path.read_text(encoding="utf-8") for name, path in SOURCE_PATHS.items()}


def function_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)
    segment = ast.get_source_segment(source, node)
    assert segment is not None
    return segment


def patient_scope_violations(sources: dict[str, str]) -> set[str]:
    dependencies = sources["dependencies"]
    patients = sources["patients"]
    violations: set[str] = set()
    required = {
        "clinic_predicate": "PatientClinicAssociation.clinic_id == clinic_id",
        "active_predicate": "PatientClinicAssociation.active.is_(True)",
        "nonenumerable_not_found": "status.HTTP_404_NOT_FOUND",
    }
    for invariant, token in required.items():
        if token not in dependencies:
            violations.add(invariant)
    if "patients_in_active_clinic_statement(context.active_clinic_id)" not in function_source(patients, "list_patients"):
        violations.add("patient_list_scope")
    if "patient = get_scoped_patient(db, patient_id, context)" not in function_source(patients, "get_patient"):
        violations.add("patient_detail_scope")
    if "stmt = patients_in_active_clinic_statement(context.active_clinic_id).where" not in function_source(patients, "possible_patient_duplicates"):
        violations.add("duplicate_scope")
    if "Patient.id.in_(patient_ids_in_active_clinic_statement(context.active_clinic_id))" not in sources["search"]:
        violations.add("search_scope")
    if 'get_scoped_patient(db, data["patient_id"], context)' not in sources["appointments"]:
        violations.add("appointment_scope")
    catalog_source = sources["catalog_governance"]
    if "get_scoped_patient(db, payload.patient_id, context)" not in function_source(catalog_source, "schedule_preview"):
        violations.add("package_preview_scope")
    if "get_scoped_patient(db, payload.patient_id, context)" not in function_source(catalog_source, "book_published_package"):
        violations.add("package_booking_scope")
    if 'get_scoped_patient(db,data["patient_id"],context)' not in sources["intake"]:
        violations.add("intake_scope")
    if 'get_patient_for_clinic(db, data["patient_id"], context.clinic_id)' not in sources["ai"]:
        violations.add("ai_scope")
    reconciliation = sources["reconciliation"]
    routes = sources["reconciliation_routes"]
    model = sources["reconciliation_model"]
    migration = sources["reconciliation_migration"]
    required_reconciliation = {
        "global_collision_gate": "find_candidates(db, snapshot)",
        "non_oib_match": 'reasons.append("name_date_of_birth")',
        "no_automatic_link": 'status == "pending_review"',
        "distinct_recheck": "find_candidates(db, item.submitted_identity_snapshot)",
        "association_uniqueness": "uq_patient_clinic_association_patient_clinic",
    }
    combined = "\n".join((reconciliation, routes, model, migration, sources["patients"]))
    for invariant, token in required_reconciliation.items():
        if token not in combined:
            violations.add(invariant)
    if '"uq_patient_identity_reconciliation_active"' not in model or 'op.create_index("uq_patient_identity_reconciliation_active"' not in migration:
        violations.add("pending_request_uniqueness")
    if "lock_pending(db, request_id)" not in function_source(routes, "approve"):
        violations.add("approve_pending_lock")
    if 'require_permission("patients.identity_reconciliation.review")' not in function_source(routes, "require_reconciliation_reviewer") or 'actor.actor_type != "user"' not in function_source(routes, "require_reconciliation_reviewer"):
        violations.add("explicit_review_permission")
    if "return PatientIdentityReviewRequired" not in function_source(sources["patients"], "create_patient"):
        violations.add("opaque_requester_response")
    forbidden_requester_tokens = ("candidate_patient_ids=item", "match_reasons=item", "requesting_institution_id=item")
    status_source = function_source(routes, "requester_out")
    if any(token in status_source for token in forbidden_requester_tokens):
        violations.add("opaque_requester_privacy")
    return violations


def mutate_once(sources: dict[str, str], file_key: str, old: str, new: str) -> dict[str, str]:
    mutated = dict(sources)
    assert old in mutated[file_key], f"mutator target missing: {file_key}: {old}"
    mutated[file_key] = mutated[file_key].replace(old, new, 1)
    assert mutated != sources, "no-op mutation must be rejected"
    return mutated


def test_patient_scope_source_contract_baseline():
    assert patient_scope_violations(load_sources()) == set()


@pytest.mark.parametrize(
    ("file_key", "old", "new", "expected_invariant"),
    [
        ("dependencies", "PatientClinicAssociation.clinic_id == clinic_id", "PatientClinicAssociation.clinic_id != clinic_id", "clinic_predicate"),
        ("dependencies", "PatientClinicAssociation.active.is_(True)", "PatientClinicAssociation.active.is_(False)", "active_predicate"),
        ("patients", "patients_in_active_clinic_statement(context.active_clinic_id)", "select(Patient)", "patient_list_scope"),
        ("patients", "patient = get_scoped_patient(db, patient_id, context)", "patient = db.get(Patient, patient_id)", "patient_detail_scope"),
        ("patients", "stmt = patients_in_active_clinic_statement(context.active_clinic_id).where", "stmt = select(Patient).where", "duplicate_scope"),
        ("search", "Patient.id.in_(patient_ids_in_active_clinic_statement(context.active_clinic_id))", "Patient.id.is_not(None)", "search_scope"),
        ("appointments", 'get_scoped_patient(db, data["patient_id"], context)', 'db.get(Patient, data["patient_id"])', "appointment_scope"),
        ("catalog_governance", "get_scoped_patient(db, payload.patient_id, context)", "db.get(Patient, payload.patient_id)", "package_preview_scope"),
        ("intake", 'get_scoped_patient(db,data["patient_id"],context)', 'db.get(Patient,data["patient_id"])', "intake_scope"),
        ("ai", 'get_patient_for_clinic(db, data["patient_id"], context.clinic_id)', 'db.get(Patient, data["patient_id"])', "ai_scope"),
    ],
)
def test_single_fault_patient_scope_mutations_are_rejected(file_key, old, new, expected_invariant):
    baseline = load_sources()
    mutated = mutate_once(baseline, file_key, old, new)

    assert patient_scope_violations(baseline) == set()
    assert patient_scope_violations(mutated) == {expected_invariant}


@pytest.mark.parametrize(
    ("file_key", "old", "new", "expected_invariant"),
    [
        ("reconciliation", "find_candidates(db, snapshot)", "([], {})", "global_collision_gate"),
        ("reconciliation", 'reasons.append("name_date_of_birth")', "pass", "non_oib_match"),
        ("reconciliation_routes", "return requester_out(approve_link(db, lock_pending(db, request_id), actor, request, payload.reason, payload.candidate_patient_id))", "return requester_out(approve_link(db, db.get(PatientIdentityReconciliationRequest, request_id), actor, request, payload.reason, payload.candidate_patient_id))", "approve_pending_lock"),
        ("reconciliation", "find_candidates(db, item.submitted_identity_snapshot)", "([], {})", "distinct_recheck"),
        ("reconciliation_model", "uq_patient_clinic_association_patient_clinic", "removed_association_uniqueness", "association_uniqueness"),
        ("reconciliation_migration", 'op.create_index("uq_patient_identity_reconciliation_active"', 'op.create_index("removed_pending_uniqueness"', "pending_request_uniqueness"),
        ("reconciliation_routes", 'actor: Actor = Depends(require_permission("patients.identity_reconciliation.review"))', "actor: Actor = Depends(get_current_actor)", "explicit_review_permission"),
        ("patients", "return PatientIdentityReviewRequired(request_id=result.id, status=result.status)", "return PatientOut.model_validate(result)", "opaque_requester_response"),
    ],
)
def test_single_fault_reconciliation_mutations_are_rejected(file_key, old, new, expected_invariant):
    baseline = load_sources()
    mutated = mutate_once(baseline, file_key, old, new)
    assert patient_scope_violations(baseline) == set()
    assert expected_invariant in patient_scope_violations(mutated)


def test_mutation_harness_rejects_noop_compound_and_duplicate_outputs():
    baseline = load_sources()
    with pytest.raises(AssertionError, match="no-op"):
        mutate_once(baseline, "patients", "from datetime import date", "from datetime import date")

    first = mutate_once(
        baseline,
        "patients",
        "patients_in_active_clinic_statement(context.active_clinic_id)",
        "select(Patient)",
    )
    compound = mutate_once(
        first,
        "ai",
        'get_patient_for_clinic(db, data["patient_id"], context.clinic_id)',
        'db.get(Patient, data["patient_id"])',
    )
    assert patient_scope_violations(compound) == {"patient_list_scope", "ai_scope"}

    duplicate = mutate_once(
        baseline,
        "patients",
        "patients_in_active_clinic_statement(context.active_clinic_id)",
        "select(Patient)",
    )
    assert first == duplicate
    assert len({tuple(sorted(first.items())), tuple(sorted(duplicate.items()))}) == 1
