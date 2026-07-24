from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_current_documentation_entrypoints_are_canonical_and_demo_safe():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    security = (ROOT / "docs" / "CURRENT_SECURITY_MODEL.md").read_text(encoding="utf-8")

    assert len(readme.splitlines()) < 120
    for name in (
        "CURRENT_PRODUCT_STATE",
        "CURRENT_ARCHITECTURE",
        "CURRENT_SECURITY_MODEL",
        "CURRENT_OPERATIONAL_LIMITATIONS",
    ):
        assert name in readme
        assert name in index
    assert "stvarne podatke" in readme
    assert "session-bound CSRF" in security
    assert "Produkcija s uključenim previewom ne" in security
