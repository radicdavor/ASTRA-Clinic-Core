from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCUMENT = ROOT / "docs" / "ux" / "focused-patient-journey-workspace.md"


def test_focused_patient_journey_documentation_preserves_workflow_boundaries() -> None:
    content = DOCUMENT.read_text(encoding="utf-8")

    assert "Progressive disclosure" in content
    assert "Source documents remain the source of truth" in content
    assert "No workflow transition, clinical gate or billing gate is bypassed" in content
    assert "Unsaved clinical-form navigation protection remains active" in content
    assert "institution/clinic scope remain backend-enforced" in content
