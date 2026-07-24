from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = REPOSITORY_ROOT / "docs" / "ux" / "operational-list-baseline.md"


def test_operational_list_baseline_covers_measurements_and_safety_boundaries() -> None:
    baseline = BASELINE_PATH.read_text(encoding="utf-8")

    for route in {"/clinical-documents", "/invoices", "/audit-log"}:
        assert route in baseline
    for viewport in {"1440 × 900", "1280 × 800", "1024 × 768"}:
        assert viewport in baseline
    for classification in {
        "PRIMARY",
        "SECONDARY",
        "DETAIL-ONLY",
        "ADVANCED-FILTER",
        "ROLE-SPECIFIC",
        "REDUNDANT",
    }:
        assert classification in baseline

    assert "Mount requestovi zaslona" in baseline
    assert "Ciljani after model" in baseline
    assert "403" in baseline
    assert "PHI-safe" in baseline
    assert "raw before/after snapshotovi" in baseline
    assert "Sakrivanje kontrole u sučelju nikada nije zamjena za backend autorizaciju" in baseline
    assert "Faza A ne tvrdi da su Faze B–G implementirane ili validirane" in baseline
