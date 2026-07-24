from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = REPOSITORY_ROOT / "docs" / "ux" / "role-preview-model.md"


def test_role_preview_model_documents_real_session_and_fail_closed_boundary():
    content = MODEL_PATH.read_text(encoding="utf-8")

    assert "kontrolirani endpoint za izdavanje nove demo browser session" in content
    assert "APP_ENV != production" in content
    assert "DEMO_PERSONA_SWITCHER_ENABLED == true" in content
    assert "`admin`" in content
    assert "`receptionist`" in content
    assert "`nurse`" in content
    assert "`physician_1`" in content
    assert "`physician_2`" in content
    assert "Proizvoljan user ID" in content
    assert "demo_persona_switched" in content
