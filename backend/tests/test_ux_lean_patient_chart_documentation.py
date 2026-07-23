from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCUMENT = ROOT / "docs" / "ux" / "lean-patient-chart.md"


def test_lean_patient_chart_documentation_preserves_clinical_security_boundaries() -> None:
    content = DOCUMENT.read_text(encoding="utf-8")

    assert "progressive disclosure" in content
    assert "Source documents remain the source of truth" in content
    assert "AI actions remain explicit and require human review" in content
    assert "No backend permission, institution scope, clinic scope or mutation rule is changed" in content
    assert "audit log" in content
