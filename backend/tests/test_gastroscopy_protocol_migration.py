from pathlib import Path


def test_gastroscopy_preparation_protocol_migration_contains_safe_draft() -> None:
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "0036_seed_gastroscopy_preparation_protocol.py"
    content = migration.read_text(encoding="utf-8")

    assert "gastroscopy-preparation-v1" in content
    assert "Priprema za gastroskopiju" in content
    assert "status)" in content and "'draft'" in content
    assert "Ne donositi automatski zaključak" in content
    assert "https://pubmed.ncbi.nlm.nih.gov/34905797/" in content
    assert content.count("(\n            \"") >= 8
