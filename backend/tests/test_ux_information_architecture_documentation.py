from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = REPOSITORY_ROOT / "docs" / "ux" / "current-screen-inventory.md"


def test_phase_a_ux_inventory_covers_required_routes_roles_and_baselines() -> None:
    inventory = INVENTORY_PATH.read_text(encoding="utf-8")

    required_routes = {
        "/",
        "/patients",
        "/patients/new",
        "/patients/:id",
        "/reception",
        "/episodes",
        "/episodes/new",
        "/episodes/:id",
        "/clinical-documents",
        "/clinical-documents/:id",
        "/laboratory",
        "/therapies",
        "/appointments",
        "/appointments/new",
        "/appointments/package",
        "/appointments/:id",
        "/journeys/:id",
        "/workflow",
        "/workflow/:id",
        "/knowledge",
        "/knowledge/:id",
        "/gastroenterology",
        "/services",
        "/clinics",
        "/modules",
        "/inventory",
        "/suppliers",
        "/purchase-orders",
        "/invoices",
        "/audit-log",
        "/api-keys",
        "/readiness",
        "/login",
        "/program1/synthetic-review",
        "/program1/synthetic-evaluation",
    }
    required_roles = {
        "Liječnik",
        "Sestra/tehničar",
        "Tajnica/administratorica recepcije",
        "Naplata",
        "Voditelj zaliha",
        "Administrator",
        "Pregledavatelj dokumenata",
    }
    required_classifications = {
        "ESSENTIAL",
        "CONTEXTUAL",
        "ADVANCED",
        "REDUNDANT",
        "HISTORICAL",
        "TECHNICAL-ONLY",
    }
    required_viewports = {
        "1440 × 900",
        "1280 × 800",
        "1024 × 768",
        "768 × 1024",
    }
    required_baselines = {
        "app-shell-dashboard-",
        "journey-workspace-",
        "patient-detail-",
        "clinical-documents-",
        "appointment-form-",
        "invoices-",
        "audit-log-",
        "readiness-",
    }

    assert INVENTORY_PATH.is_file()
    assert required_routes.issubset(set(inventory.split("`")[1::2]))
    for role in required_roles:
        assert role in inventory
    for classification in required_classifications:
        assert classification in inventory
    for viewport in required_viewports:
        assert viewport in inventory
    for baseline in required_baselines:
        assert baseline in inventory
    assert "Sigurnosne i kliničke regresije" in inventory
    assert "Faza A ne mijenja rute, API-je, autorizaciju" in inventory
