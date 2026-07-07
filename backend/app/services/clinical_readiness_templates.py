from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class ClinicalReadinessTemplateItem:
    key: str
    label: str
    category: str
    default_status: str
    severity: str
    responsible_role: str
    source_type: str
    suggested_action: str
    blocking: bool = False
    override_allowed: bool = False
    override_role: str | None = None
    override_reason_required: bool = False
    audit_required: bool = False


@dataclass(frozen=True)
class ClinicalReadinessTemplate:
    key: str
    name: str
    specific: bool
    items: tuple[ClinicalReadinessTemplateItem, ...]


@dataclass(frozen=True)
class ClinicalReadinessTemplateSelection:
    template: ClinicalReadinessTemplate
    binding_status: str
    binding_warning: str


KEYWORD_BINDING_WARNING = "Template je odabran demo/pilot keyword matchingom prema nazivu usluge."
GENERIC_BINDING_WARNING = "Nema specificnog template matcha; koristi se genericki demo/pilot template."


def _item(
    key: str,
    label: str,
    category: str,
    default_status: str,
    severity: str,
    responsible_role: str,
    suggested_action: str,
    *,
    source_type: str = "system_record",
    blocking: bool = False,
) -> ClinicalReadinessTemplateItem:
    return ClinicalReadinessTemplateItem(
        key=key,
        label=label,
        category=category,
        default_status=default_status,
        severity=severity,
        responsible_role=responsible_role,
        source_type=source_type,
        suggested_action=suggested_action,
        blocking=blocking,
    )


GENERIC_TEMPLATE = ClinicalReadinessTemplate(
    key="generic",
    name="Genericki clinical readiness preview",
    specific=False,
    items=(
        _item(
            "generic_confirm_planned_service",
            "Potvrditi planiranu uslugu",
            "service",
            "ready_with_warning",
            "info",
            "admin",
            "Provjeriti odgovara li planirana usluga terminu i pacijentu.",
        ),
        _item(
            "generic_confirm_consent_need",
            "Provjeriti treba li pristanak",
            "consent",
            "needs_consent",
            "warning",
            "nurse",
            "Provjeriti postoji li potreba za pristankom prema lokalnom toku rada. Ovo nije clearance.",
        ),
    ),
)


GASTROSCOPY_TEMPLATE = ClinicalReadinessTemplate(
    key="gastroscopy",
    name="Gastroskopija",
    specific=True,
    items=(
        _item("gastroscopy_fasting_check", "Provjera nataste", "preparation", "needs_nurse_action", "warning", "nurse", "Provjeriti je li status nataste dokumentiran ili klinicki pregledan."),
        _item("gastroscopy_medication_risk", "Pregled antikoagulansa/antiagregansa", "medication", "needs_physician_review", "warning", "physician", "Pregledati lijekove koji mogu utjecati na postupak. Preview ne donosi odluku."),
        _item("gastroscopy_allergy_review", "Pregled alergija", "allergy", "needs_physician_review", "warning", "physician", "Provjeriti poznate alergije prije postupka."),
        _item("gastroscopy_sedation_escort", "Pratnja nakon sedacije ako je sedacija planirana", "sedation_anesthesia", "needs_nurse_action", "warning", "nurse", "Provjeriti postoji li pratnja ako je sedacija dio plana."),
        _item("gastroscopy_consent", "Provjera pristanka za gastroskopiju/sedaciju", "consent", "needs_consent", "warning", "nurse", "Provjeriti je li pristanak prisutan prema lokalnom toku rada."),
        _item("gastroscopy_previous_findings", "Pregled prethodnih relevantnih nalaza", "reviewed_evidence", "needs_physician_review", "warning", "physician", "Pregledati dostupne pregledane nalaze ako postoje."),
    ),
)


COLONOSCOPY_TEMPLATE = ClinicalReadinessTemplate(
    key="colonoscopy",
    name="Kolonoskopija",
    specific=True,
    items=(
        _item("colonoscopy_bowel_prep", "Deklaracija pripreme crijeva", "preparation", "needs_nurse_action", "warning", "nurse", "Provjeriti je li priprema crijeva deklarirana ili pregledana."),
        _item("colonoscopy_anticoagulant_review", "Pregled antikoagulansa/antiagregansa", "medication", "needs_physician_review", "warning", "physician", "Pregledati lijekove koji mogu utjecati na kolonoskopiju ili polipektomiju."),
        _item("colonoscopy_diabetes_medication", "Pregled terapije za dijabetes ako je relevantno", "medication", "needs_physician_review", "warning", "physician", "Pregledati terapiju za dijabetes ako postoji u izvorima ili anamnezi."),
        _item("colonoscopy_sedation_escort", "Pratnja nakon sedacije", "sedation_anesthesia", "needs_nurse_action", "warning", "nurse", "Provjeriti pratnju nakon sedacije prema lokalnom toku rada."),
        _item("colonoscopy_consent", "Pristanak za kolonoskopiju/sedaciju/polipektomiju", "consent", "needs_consent", "warning", "nurse", "Provjeriti prisutnost potrebnog pristanka. Preview ne odobrava postupak."),
        _item("colonoscopy_prior_colonoscopy_phd", "Pregled prethodne kolonoskopije/PHD nalaza", "reviewed_evidence", "needs_physician_review", "warning", "physician", "Pregledati prethodne pregledane izvore ako postoje."),
        _item("colonoscopy_family_high_risk", "Obiteljska anamneza ili high-risk pregled", "procedure_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati postoji li relevantan high-risk kontekst."),
        _item("colonoscopy_polypectomy_materials", "Material readiness za polipektomijski pribor", "inventory_material", "ready_with_warning", "warning", "nurse", "Provjeriti dostupnost potrebnog pribora ako je polipektomija moguca."),
    ),
)


HPYLORI_TEMPLATE = ClinicalReadinessTemplate(
    key="hpylori",
    name="H. pylori",
    specific=True,
    items=(
        _item("hpylori_prior_therapy", "Poznata prethodna eradikacijska terapija", "reviewed_evidence", "needs_physician_review", "warning", "physician", "Pregledati postoje li izvori o prethodnoj terapiji."),
        _item("hpylori_penicillin_allergy", "Pregled alergije na penicilin", "allergy", "needs_physician_review", "warning", "physician", "Provjeriti alergiju na penicilin prije odluke o terapiji."),
        _item("hpylori_timing_review", "Pregled PPI/antibiotik/bizmut timinga", "medication", "needs_physician_review", "warning", "physician", "Pregledati timing lijekova i testiranja. Preview ne propisuje terapiju."),
        _item("hpylori_test_of_cure", "Timing test-of-cure", "procedure_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati plan kontrole eradikacije ako je relevantan."),
        _item("hpylori_failure_resistance", "Prethodni neuspjeh ili rezistencija", "reviewed_evidence", "needs_physician_review", "warning", "physician", "Pregledati postoji li dokumentiran prethodni neuspjeh ili rezistencija."),
    ),
)


AESTHETIC_INJECTABLE_TEMPLATE = ClinicalReadinessTemplate(
    key="aesthetic_injectable",
    name="Estetski injektivni tretman",
    specific=True,
    items=(
        _item("injectable_pregnancy_breastfeeding", "Trudnoca/dojenje deklaracija", "aesthetic_treatment_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati status trudnoce/dojenja gdje je relevantno."),
        _item("injectable_active_infection", "Aktivna infekcija/herpes provjera", "aesthetic_treatment_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati postoji li aktivna infekcija ili herpes."),
        _item("injectable_anticoagulant_review", "Pregled antikoagulansa", "medication", "needs_physician_review", "warning", "physician", "Pregledati lijekove s rizikom krvarenja ili modrica."),
        _item("injectable_allergy_review", "Pregled alergija", "allergy", "needs_physician_review", "warning", "physician", "Provjeriti poznate alergije."),
        _item("injectable_prior_material_history", "Prethodni filler/material history", "reviewed_evidence", "needs_physician_review", "warning", "physician", "Pregledati prethodne materijale ako su dokumentirani."),
        _item("injectable_prior_complication", "Prethodne komplikacije", "reviewed_evidence", "needs_physician_review", "warning", "physician", "Pregledati prethodne komplikacije ako postoje."),
        _item("injectable_consent", "Pristanak za tretman", "consent", "needs_consent", "warning", "nurse", "Provjeriti pristanak prema lokalnom toku rada."),
        _item("injectable_baseline_photo", "Baseline foto dokumentacija", "administrative", "ready_with_warning", "warning", "admin", "Provjeriti je li foto dokumentacija prisutna ako je dio toka rada."),
        _item("injectable_product_batch", "Dostupnost proizvoda/serije", "inventory_material", "ready_with_warning", "warning", "nurse", "Provjeriti proizvod i seriju prije tretmana."),
    ),
)


AESTHETIC_SKINBOOSTER_PN_TEMPLATE = ClinicalReadinessTemplate(
    key="aesthetic_skinbooster_pn",
    name="Skinbooster / polinukleotid",
    specific=True,
    items=(
        _item("skinbooster_active_infection", "Aktivna infekcija provjera", "aesthetic_treatment_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati postoji li aktivna infekcija."),
        _item("skinbooster_autoimmune_review", "Inflammatory/autoimmune concern pregled", "aesthetic_treatment_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati relevantne upalne ili autoimune okolnosti ako postoje."),
        _item("skinbooster_prior_reaction", "Prethodna reakcija", "reviewed_evidence", "needs_physician_review", "warning", "physician", "Pregledati prethodne reakcije ako su dokumentirane."),
        _item("skinbooster_treatment_interval", "Interval tretmana", "procedure_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati interval prethodnog i planiranog tretmana."),
        _item("skinbooster_consent", "Pristanak za tretman", "consent", "needs_consent", "warning", "nurse", "Provjeriti pristanak prema lokalnom toku rada."),
        _item("skinbooster_photo_documentation", "Foto dokumentacija", "administrative", "ready_with_warning", "warning", "admin", "Provjeriti foto dokumentaciju ako je dio toka rada."),
        _item("skinbooster_product_batch", "Dostupnost proizvoda/serije", "inventory_material", "ready_with_warning", "warning", "nurse", "Provjeriti proizvod i seriju prije tretmana."),
    ),
)


AESTHETIC_ENERGY_DEVICE_TEMPLATE = ClinicalReadinessTemplate(
    key="aesthetic_energy_device",
    name="Estetski energy-device tretman",
    specific=True,
    items=(
        _item("energy_device_implant_pacemaker", "Kontraindicirani uredaj/implantat/pacemaker provjera", "aesthetic_treatment_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati relevantne uredaje ili implantate gdje je primjenjivo."),
        _item("energy_device_skin_condition", "Stanje koze u tretiranom podrucju", "aesthetic_treatment_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati stanje koze u podrucju tretmana."),
        _item("energy_device_recent_procedures", "Nedavni postupci", "procedure_specific_risk", "needs_physician_review", "warning", "physician", "Pregledati nedavne postupke koji mogu biti relevantni."),
        _item("energy_device_consent", "Pristanak za tretman", "consent", "needs_consent", "warning", "nurse", "Provjeriti pristanak prema lokalnom toku rada."),
        _item("energy_device_area_documentation", "Dokumentacija tretiranog podrucja", "administrative", "ready_with_warning", "warning", "admin", "Provjeriti dokumentaciju tretiranog podrucja ako je dio toka rada."),
    ),
)


TEMPLATES = {
    GENERIC_TEMPLATE.key: GENERIC_TEMPLATE,
    GASTROSCOPY_TEMPLATE.key: GASTROSCOPY_TEMPLATE,
    COLONOSCOPY_TEMPLATE.key: COLONOSCOPY_TEMPLATE,
    HPYLORI_TEMPLATE.key: HPYLORI_TEMPLATE,
    AESTHETIC_INJECTABLE_TEMPLATE.key: AESTHETIC_INJECTABLE_TEMPLATE,
    AESTHETIC_SKINBOOSTER_PN_TEMPLATE.key: AESTHETIC_SKINBOOSTER_PN_TEMPLATE,
    AESTHETIC_ENERGY_DEVICE_TEMPLATE.key: AESTHETIC_ENERGY_DEVICE_TEMPLATE,
}


def normalize_service_name(service_name: str | None) -> str:
    if not service_name:
        return ""
    decomposed = unicodedata.normalize("NFKD", service_name)
    ascii_text = "".join(character for character in decomposed if not unicodedata.combining(character))
    return ascii_text.casefold()


def _has_word(text: str, word: str) -> bool:
    return bool(re.search(rf"(^|[^a-z0-9]){re.escape(word)}([^a-z0-9]|$)", text))


def keyword_selection(template: ClinicalReadinessTemplate) -> ClinicalReadinessTemplateSelection:
    return ClinicalReadinessTemplateSelection(
        template=template,
        binding_status="keyword_fallback",
        binding_warning=KEYWORD_BINDING_WARNING,
    )


def generic_selection() -> ClinicalReadinessTemplateSelection:
    return ClinicalReadinessTemplateSelection(
        template=GENERIC_TEMPLATE,
        binding_status="generic_fallback",
        binding_warning=GENERIC_BINDING_WARNING,
    )


def select_clinical_readiness_template(service_name: str | None) -> ClinicalReadinessTemplateSelection:
    normalized = normalize_service_name(service_name)

    if "kolonoskop" in normalized:
        return keyword_selection(COLONOSCOPY_TEMPLATE)
    if "gastroskop" in normalized:
        return keyword_selection(GASTROSCOPY_TEMPLATE)
    if "h. pylori" in normalized or "helicobacter" in normalized or "hpylori" in normalized:
        return keyword_selection(HPYLORI_TEMPLATE)
    if "skinbooster" in normalized or "polinukleotid" in normalized or _has_word(normalized, "pn"):
        return keyword_selection(AESTHETIC_SKINBOOSTER_PN_TEMPLATE)
    if "laser" in normalized or _has_word(normalized, "rf") or "exion" in normalized or "energy" in normalized:
        return keyword_selection(AESTHETIC_ENERGY_DEVICE_TEMPLATE)
    if "filler" in normalized or "botox" in normalized:
        return keyword_selection(AESTHETIC_INJECTABLE_TEMPLATE)

    return generic_selection()
