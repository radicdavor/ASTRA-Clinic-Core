"""Fail-closed route inventory for the PR #3 security contexts.

This is a test-only snapshot, not a runtime authorization framework. Every
registered /api route receives one review classification and contributes to a
stable fingerprint. Adding, removing, moving, or reclassifying a route requires
an explicit inventory review and fingerprint update.
"""

from hashlib import sha256

from app.main import app


GLOBAL_IDENTITY = "GlobalIdentityContext"
CLINIC_OPERATIONAL = "ClinicOperationalContext"
CLINIC_BILLING = "ClinicBillingContext"
INSTITUTION_CLINICAL = "InstitutionClinicalContext"
SYSTEM_SECURITY_AUDIT = "SystemSecurityAuditContext"
NON_SENSITIVE = "NonSensitiveOrLocalContext"


MODULE_DEFAULT_CONTEXT = {
    "ai": GLOBAL_IDENTITY,
    "appointments": CLINIC_OPERATIONAL,
    "audit": SYSTEM_SECURITY_AUDIT,
    "catalog": CLINIC_OPERATIONAL,
    "catalog_governance": CLINIC_OPERATIONAL,
    "clinical_documents": INSTITUTION_CLINICAL,
    "clinical_forms": INSTITUTION_CLINICAL,
    "daily_dashboard": CLINIC_OPERATIONAL,
    "document_ingestion": INSTITUTION_CLINICAL,
    "episodes": INSTITUTION_CLINICAL,
    "intake": CLINIC_OPERATIONAL,
    "inventory": CLINIC_OPERATIONAL,
    "journey_activities": CLINIC_OPERATIONAL,
    "journey_check_in": CLINIC_OPERATIONAL,
    "journey_closure": CLINIC_OPERATIONAL,
    "journey_encounter": INSTITUTION_CLINICAL,
    "journey_preparation": CLINIC_OPERATIONAL,
    "journey_timeline": INSTITUTION_CLINICAL,
    "knowledge": NON_SENSITIVE,
    "laboratory": INSTITUTION_CLINICAL,
    "pathology": INSTITUTION_CLINICAL,
    "patient_clinical_summary": INSTITUTION_CLINICAL,
    "patient_journeys": CLINIC_OPERATIONAL,
    "patients": GLOBAL_IDENTITY,
    "readiness": SYSTEM_SECURITY_AUDIT,
    "reception": CLINIC_OPERATIONAL,
    "reports": INSTITUTION_CLINICAL,
    "search": GLOBAL_IDENTITY,
    "system": NON_SENSITIVE,
    "therapies": INSTITUTION_CLINICAL,
    "workflow": INSTITUTION_CLINICAL,
}

# Updating this value requires reviewing the full sorted route/context snapshot
# emitted by `_registry_rows()`, not merely accepting a new hash.
EXPECTED_API_ROUTE_REGISTRY_SHA256 = "ab07c1922bced326e79372dc93b21bfac8a3e4a23e7b2acf2bd7b6d1ffe50cbc"
EXPECTED_API_ROUTE_METHOD_COUNT = 261


def _scope_for_route(module_name: str, path: str) -> str | None:
    if module_name == "inventory" and (
        path.startswith("/api/invoices")
        or path == "/api/appointments/{appointment_id}/draft-invoice"
    ):
        return CLINIC_BILLING
    if module_name == "journey_closure" and (
        "/billing/" in path
        or path.endswith("/payments")
        or path.endswith("/payments/defer")
    ):
        return CLINIC_BILLING
    if module_name == "patients":
        if path == "/api/patients/{patient_id}/invoices":
            return CLINIC_BILLING
        if any(
            marker in path
            for marker in (
                "/clinical-record",
                "/clinical-findings",
                "/clinical-open-questions",
                "/clinical-evidence-timeline",
                "/episodes",
            )
        ):
            return INSTITUTION_CLINICAL
    return MODULE_DEFAULT_CONTEXT.get(module_name)


def _registry_rows() -> list[str]:
    rows: list[str] = []
    unclassified: list[str] = []
    for route in app.routes:
        if not route.path.startswith("/api"):
            continue
        endpoint = getattr(route, "endpoint", None)
        module_name = getattr(endpoint, "__module__", "").rsplit(".", 1)[-1]
        context = _scope_for_route(module_name, route.path)
        methods = (getattr(route, "methods", set()) or set()) - {"HEAD", "OPTIONS"}
        for method in methods:
            if context is None:
                unclassified.append(f"{method} {route.path} ({module_name})")
            else:
                rows.append(f"{method} {route.path} [{context}]")
    assert not unclassified, f"Neklasificirane /api rute: {sorted(unclassified)}"
    return sorted(rows)


def test_every_api_route_is_reviewed_and_registry_is_fail_closed():
    rows = _registry_rows()

    assert len(rows) == EXPECTED_API_ROUTE_METHOD_COUNT
    assert len(rows) == len(set(rows))
    fingerprint = sha256("\n".join(rows).encode("utf-8")).hexdigest()
    assert fingerprint == EXPECTED_API_ROUTE_REGISTRY_SHA256, (
        "Promijenjen je API route/scope registry. Pregledajte puni route diff i "
        "ažurirajte docs/security-scope-inventory.md prije prihvaćanja novog fingerprinta."
    )


def test_journey_closure_financial_mutations_are_billing_scoped():
    rows = set(_registry_rows())

    assert (
        "POST /api/patient-journeys/{journey_id}/billing/prepare "
        "[ClinicBillingContext]"
    ) in rows
    assert (
        "POST /api/patient-journeys/{journey_id}/payments "
        "[ClinicBillingContext]"
    ) in rows
    assert (
        "POST /api/patient-journeys/{journey_id}/payments/defer "
        "[ClinicBillingContext]"
    ) in rows
