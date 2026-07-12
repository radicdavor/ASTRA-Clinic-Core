"""Add expanded laboratory template catalog.

Revision ID: 0031_add_laboratory_template_catalog
Revises: 0030_add_bloating_lab_template
"""
import json
from alembic import op
import sqlalchemy as sa

revision = "0031_add_laboratory_template_catalog"
down_revision = "0030_add_bloating_lab_template"
branch_labels = None
depends_on = None

TEMPLATES = [
    ("Debljina — kontrolni pregled", "Debljina i metabolizam", "Kontrolni metabolički panel; liječnik prilagođava opseg kliničkom tijeku.", ["Glukoza", "HbA1c", "Inzulin", "Lipidogram", "ALT", "AST", "GGT", "Kreatinin", "TSH"]),
    ("Metabolički sindrom", "Debljina i metabolizam", "Početni panel za liječničku obradu metaboličkog sindroma.", ["Glukoza", "HbA1c", "Lipidogram", "ALT", "AST", "GGT", "Kreatinin", "Mokraćna kiselina"]),
    ("Predijabetes i inzulinska rezistencija", "Debljina i metabolizam", "Osnovni panel; uvjete uzorkovanja i tumačenje određuje liječnik.", ["Glukoza natašte", "Inzulin natašte", "HbA1c", "Lipidogram"]),
    ("Alopecija — proširena obrada", "Alopecija", "Prošireni laboratorijski panel za liječničku obradu alopecije.", ["KKS", "Feritin", "Željezo", "TIBC/UIBC", "TSH", "Vitamin D", "Vitamin B12", "Folat", "Cink"]),
    ("Umor — početna obrada", "Opći simptomi", "Početni panel za liječničku obradu umora.", ["KKS", "CRP", "Glukoza", "TSH", "Feritin", "Vitamin B12", "Folat", "Vitamin D", "Kreatinin", "ALT", "AST"]),
    ("Anemija — početna obrada", "Hematologija", "Početni panel za liječničku obradu moguće anemije.", ["KKS", "Retikulociti", "Feritin", "Željezo", "TIBC/UIBC", "Vitamin B12", "Folat", "CRP"]),
    ("Štitnjača — početna obrada", "Endokrinologija", "Osnovno uključuje TSH i FT4. FT3, anti-TPO i anti-Tg dodaju se samo prema liječničkoj procjeni.", ["TSH", "FT4"]),
    ("Jetreni panel", "Gastroenterologija", "Osnovni laboratorijski panel jetrene funkcije.", ["ALT", "AST", "GGT", "ALP", "Bilirubin ukupni", "Bilirubin direktni", "Albumin"]),
    ("Bubrežna funkcija", "Nefrologija", "Osnovni panel bubrežne funkcije i urina.", ["Kreatinin", "eGFR", "Ureja", "Natrij", "Kalij", "Urin", "Albumin/kreatinin u urinu"]),
    ("Lipidni status", "Debljina i metabolizam", "Osnovno uključuje standardni lipidni status. ApoB i Lp(a) dodaju se samo prema indikaciji.", ["Ukupni kolesterol", "LDL", "HDL", "Trigliceridi"]),
    ("PCOS — početna obrada", "Endokrinologija", "Osnovni metabolički panel. Dodatne hormonske pretrage određuje liječnik prema kliničkoj slici i danu ciklusa.", ["Glukoza", "HbA1c", "Lipidogram", "TSH"]),
    ("Akne i hiperandrogenizam", "Dermatologija", "TSH je početna stavka; hormonske pretrage dodaje liječnik prema kliničkoj procjeni i danu ciklusa.", ["TSH"]),
    ("Priprema za endoskopiju", "Gastroenterologija", "Pretrage se koriste samo kada su klinički indicirane prije endoskopskog zahvata.", ["KKS", "Koagulacija", "Kreatinin", "Elektroliti"]),
    ("Kronična upalna bolest crijeva — kontrola", "Gastroenterologija", "Kontrolni panel za liječničko praćenje kronične upalne bolesti crijeva.", ["KKS", "CRP", "Feritin", "Albumin", "ALT", "AST", "Kreatinin", "Fekalni kalprotektin"]),
    ("Celijakija — početna obrada", "Gastroenterologija", "Osnovno uključuje tTG-IgA i ukupni IgA. Daljnje testove određuje liječnik.", ["tTG-IgA", "Ukupni IgA"]),
    ("Malapsorpcija i nutritivni status", "Gastroenterologija", "Panel za liječničku procjenu malapsorpcije i nutritivnog statusa.", ["KKS", "Feritin", "Vitamin B12", "Folat", "Vitamin D", "Albumin", "Kalcij", "Magnezij"]),
    ("Preventivni pregled — osnovni", "Preventiva", "Osnovni preventivni panel koji liječnik prilagođava dobi, spolu i individualnim rizicima.", ["KKS", "Glukoza", "Lipidogram", "Kreatinin", "ALT", "AST", "Urin"]),
]

def upgrade() -> None:
    statement = sa.text("""
        INSERT INTO lab_templates (name, condition, description, tests, active)
        VALUES (:name, :condition, :description, CAST(:tests AS JSON), true)
        ON CONFLICT (name) DO UPDATE SET
          condition=EXCLUDED.condition, description=EXCLUDED.description,
          tests=EXCLUDED.tests, active=true, updated_at=now()
    """)
    connection = op.get_bind()
    for name, condition, description, tests in TEMPLATES:
        connection.execute(statement, {"name": name, "condition": condition, "description": description, "tests": json.dumps([{"test_name": test} for test in tests], ensure_ascii=False)})

def downgrade() -> None:
    names = [name for name, *_ in TEMPLATES]
    op.get_bind().execute(sa.text("DELETE FROM lab_templates WHERE name = ANY(:names)"), {"names": names})
