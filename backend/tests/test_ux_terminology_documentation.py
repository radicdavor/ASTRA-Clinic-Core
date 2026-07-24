from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TERMINOLOGY_PATH = REPOSITORY_ROOT / "docs" / "ux" / "terminology-map.md"


def test_phase_b_terminology_map_preserves_internal_contracts_and_safety_meaning() -> None:
    terminology = TERMINOLOGY_PATH.read_text(encoding="utf-8")

    for internal_term in (
        "PatientJourney",
        "JourneyActivity",
        "ClinicalEpisode",
        "ClinicalPlan",
        "ClinicalFinding",
        "EvidenceTimeline",
        "ClinicalSummary",
        "Readiness",
        "Workflow",
        "ClinicalProvenance",
    ):
        assert f"`{internal_term}`" in terminology

    for canonical_label in (
        "Tijek dolaska pacijenta",
        "Aktivnost dolaska",
        "Klinička epizoda",
        "Nalaz povezan s izvorom",
        "Klinička vremenska crta",
        "AI skica",
        "Karton pacijenta",
        "podrijetlo kliničkog podatka",
    ):
        assert canonical_label in terminology

    for safety_boundary in (
        "nisu dijagnoza ni izvor istine",
        "liječnički pregled ostaje obvezan",
        "ne stvara zadatak",
        "ne šalje poruku",
        "API putanje, request/response polja, enum vrijednosti",
    ):
        assert safety_boundary in terminology
