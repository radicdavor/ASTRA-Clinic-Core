from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCUMENT = ROOT / "docs" / "ux" / "role-based-navigation.md"


def test_role_navigation_documentation_preserves_security_boundary() -> None:
    content = DOCUMENT.read_text(encoding="utf-8")

    assert "najviše pet ulaza prve razine" in content
    assert "Skrivena poveznica nije sigurnosna kontrola" in content
    assert "require_permission" in content
    assert "require_active_clinic" in content
    assert "session/CSRF" in content
    assert "ne mijenja RBAC" in content
