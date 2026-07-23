"""Lightweight guard for PR #3 high-risk route scope registration.

This is intentionally a static regression map, not a runtime authorization
framework. Adding or removing a billing, episode/plan, patient-derived, or
audit endpoint requires an explicit scope decision here and in
docs/security-scope-inventory.md.
"""

from app.main import app


GLOBAL_IDENTITY = "GlobalIdentityContext"
CLINIC_BILLING = "ClinicBillingContext"
INSTITUTION_CLINICAL = "InstitutionClinicalContext"
SYSTEM_SECURITY_AUDIT = "SystemSecurityAuditContext"


EXPECTED_HIGH_RISK_ROUTES = {
    # Global identity and patient projections.
    ("POST", "/api/patients", GLOBAL_IDENTITY),
    ("GET", "/api/patients", GLOBAL_IDENTITY),
    ("GET", "/api/patients/possible-duplicates", GLOBAL_IDENTITY),
    ("GET", "/api/patients/{patient_id}", GLOBAL_IDENTITY),
    ("PATCH", "/api/patients/{patient_id}", GLOBAL_IDENTITY),
    ("GET", "/api/patients/{patient_id}/appointments", GLOBAL_IDENTITY),
    ("GET", "/api/patients/{patient_id}/clinical-record", INSTITUTION_CLINICAL),
    ("GET", "/api/patients/{patient_id}/clinical-findings", INSTITUTION_CLINICAL),
    ("GET", "/api/patients/{patient_id}/clinical-findings/{finding_id}", INSTITUTION_CLINICAL),
    ("GET", "/api/patients/{patient_id}/clinical-open-questions", INSTITUTION_CLINICAL),
    ("GET", "/api/patients/{patient_id}/clinical-open-questions/{question_id}", INSTITUTION_CLINICAL),
    ("GET", "/api/patients/{patient_id}/clinical-evidence-timeline", INSTITUTION_CLINICAL),
    ("GET", "/api/patients/{patient_id}/episodes", INSTITUTION_CLINICAL),
    ("GET", "/api/patients/{patient_id}/invoices", CLINIC_BILLING),
    # Episodes and plans.
    ("GET", "/api/episodes", INSTITUTION_CLINICAL),
    ("POST", "/api/episodes", INSTITUTION_CLINICAL),
    ("GET", "/api/episodes/{episode_id}", INSTITUTION_CLINICAL),
    ("PATCH", "/api/episodes/{episode_id}", INSTITUTION_CLINICAL),
    ("POST", "/api/episodes/{episode_id}/close", INSTITUTION_CLINICAL),
    ("GET", "/api/episodes/{episode_id}/appointments", INSTITUTION_CLINICAL),
    ("GET", "/api/episodes/{episode_id}/clinical-plans", INSTITUTION_CLINICAL),
    ("GET", "/api/episodes/{episode_id}/clinical-plans/active", INSTITUTION_CLINICAL),
    ("POST", "/api/episodes/{episode_id}/clinical-plans/generate", INSTITUTION_CLINICAL),
    ("PATCH", "/api/clinical-plans/{plan_id}", INSTITUTION_CLINICAL),
    ("POST", "/api/clinical-plans/{plan_id}/reject", INSTITUTION_CLINICAL),
    ("POST", "/api/clinical-plans/{plan_id}/confirm", INSTITUTION_CLINICAL),
    ("GET", "/api/episodes/{episode_id}/clinical-timeline", INSTITUTION_CLINICAL),
    # Billing and payments.
    ("GET", "/api/invoices", CLINIC_BILLING),
    ("POST", "/api/invoices", CLINIC_BILLING),
    ("GET", "/api/invoices/{invoice_id}", CLINIC_BILLING),
    ("PATCH", "/api/invoices/{invoice_id}", CLINIC_BILLING),
    ("POST", "/api/appointments/{appointment_id}/draft-invoice", CLINIC_BILLING),
    ("POST", "/api/invoices/{invoice_id}/issue", CLINIC_BILLING),
    ("GET", "/api/invoices/{invoice_id}/lines", CLINIC_BILLING),
    ("POST", "/api/invoices/{invoice_id}/lines", CLINIC_BILLING),
    ("PATCH", "/api/invoices/{invoice_id}/lines/{line_id}", CLINIC_BILLING),
    ("DELETE", "/api/invoices/{invoice_id}/lines/{line_id}", CLINIC_BILLING),
    ("POST", "/api/invoices/{invoice_id}/payments", CLINIC_BILLING),
    ("GET", "/api/invoices/{invoice_id}/payments", CLINIC_BILLING),
    ("POST", "/api/invoices/{invoice_id}/mark-paid", CLINIC_BILLING),
    # Audit.
    ("POST", "/api/audit/access-events", SYSTEM_SECURITY_AUDIT),
    ("GET", "/api/audit-log", SYSTEM_SECURITY_AUDIT),
}


def _scope_for_route(module_name: str, method: str, path: str) -> str | None:
    if module_name == "episodes":
        return INSTITUTION_CLINICAL
    if module_name == "audit":
        return SYSTEM_SECURITY_AUDIT
    if module_name == "inventory" and (
        path.startswith("/api/invoices")
        or path == "/api/appointments/{appointment_id}/draft-invoice"
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
        return GLOBAL_IDENTITY
    return None


def test_high_risk_routes_have_an_explicit_security_context_registration():
    actual: set[tuple[str, str, str]] = set()
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        module_name = getattr(endpoint, "__module__", "").rsplit(".", 1)[-1]
        methods = (getattr(route, "methods", set()) or set()) - {"HEAD", "OPTIONS"}
        for method in methods:
            context = _scope_for_route(module_name, method, route.path)
            if context:
                actual.add((method, route.path, context))

    assert actual == EXPECTED_HIGH_RISK_ROUTES
