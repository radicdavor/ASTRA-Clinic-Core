from __future__ import annotations


def extract_document_knowledge_from_text(raw_text: str | None) -> dict:
    text = (raw_text or "").lower()
    findings: list[str] = []
    recommendations: list[str] = []
    summary = "AI prijedlog: dokument nema dovoljno teksta za strukturirani sazetak. Manual review recommended."

    if "gerb" in text or "refluks" in text:
        findings.append("GERB/refluks naveden u dokumentu")
    if "adenom" in text or "polip" in text:
        findings.append("Prethodni polip/adenom naveden u dokumentu")
    if "h. pylori" in text or "helicobacter" in text:
        findings.append("H. pylori status naveden u dokumentu")
    if "gastroskop" in text:
        findings.append("Gastroskopija dokumentirana")
    if "kolonoskop" in text:
        findings.append("Kolonoskopija dokumentirana")
    if "patolog" in text or "biops" in text or "ph nalaz" in text:
        findings.append("Patologija/biopsija spomenuta u dokumentu")
    if "esomeprazol" in text or "pantoprazol" in text:
        findings.append("Terapija inhibitorom protonske pumpe spomenuta u dokumentu")
    if "kontrol" in text or "ponov" in text or "preporuc" in text:
        recommendations.append("Dokument sadrzi preporuku ili kontrolu koju treba lijecnik pregledati")
    if "patologija pending" in text or "ceka se" in text or "pending" in text:
        recommendations.append("Postoji otvoreno pitanje koje ceka nalaz ili rucni pregled")

    if findings or recommendations:
        summary = "AI prijedlog: strukturirani elementi su izdvojeni iz teksta dokumenta i cekaju lijecnicki pregled."
    return {
        "ai_summary": summary,
        "key_findings": findings,
        "recommendations": recommendations,
        "confidence": 0.72 if findings or recommendations else 0.38,
        "extraction_notes": "Deterministicki placeholder, nije stvarni AI/OCR provider.",
    }
