from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_migration():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "0037_seed_gastroenterology_operational_protocols.py"
    spec = spec_from_file_location("gastro_protocol_seed", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_requested_gastroenterology_protocols_are_safe_drafts() -> None:
    migration = load_migration()
    assert len(migration.PROTOCOLS) == 7
    assert len({protocol["key"] for protocol in migration.PROTOCOLS}) == 7
    assert all(len(protocol["rules"]) == 6 for protocol in migration.PROTOCOLS)
    assert all(protocol["source_url"].startswith("https://") for protocol in migration.PROTOCOLS)

    titles = {protocol["title"] for protocol in migration.PROTOCOLS}
    assert titles == {
        "Priprema za kolonoskopiju",
        "Postupanje s biopsijskim uzorkom",
        "Čišćenje i evidencija endoskopa",
        "Kontrola pacijenta nakon sedacije",
        "Postupanje kod nedovoljne pripreme crijeva",
        "Unos i pregled patohistološkog nalaza",
        "Postupak kod terapije koja povećava rizik krvarenja",
    }

    guidance = " ".join(rule[2] for protocol in migration.PROTOCOLS for rule in protocol["rules"])
    assert "bez dokumentirane liječničke odluke" in guidance
    assert "Ova lista sama ne odobrava otpust" in guidance
    assert "sustav ne zakazuje automatski" in guidance
    assert "sustav ne izvodi dijagnozu" in guidance
