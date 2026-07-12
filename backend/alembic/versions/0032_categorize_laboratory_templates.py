"""Categorize laboratory templates for the UI.

Revision ID: 0032_categorize_laboratory_templates
Revises: 0031_add_laboratory_template_catalog
"""
from alembic import op
import sqlalchemy as sa

revision="0032_categorize_laboratory_templates"
down_revision="0031_add_laboratory_template_catalog"
branch_labels=None
depends_on=None

GROUPS={
 "Metabolizam":["Debljina — prvi pregled","Debljina — kontrolni pregled","Metabolički sindrom","Predijabetes i inzulinska rezistencija","Lipidni status","Bubrežna funkcija"],
 "Kosa i koža":["Alopecija — početna obrada","Alopecija — proširena obrada","Akne i hiperandrogenizam"],
 "Gastroenterologija":["Nadutost — početna obrada","Jetreni panel","Priprema za endoskopiju","Kronična upalna bolest crijeva — kontrola","Celijakija — početna obrada"],
 "Endokrinologija":["Štitnjača — početna obrada","PCOS — početna obrada"],
 "Nutritivni status":["Umor — početna obrada","Anemija — početna obrada","Malapsorpcija i nutritivni status"],
 "Preventiva":["Preventivni pregled — osnovni"],
}

def upgrade():
    op.add_column("lab_templates",sa.Column("category",sa.String(80),nullable=False,server_default="Preventiva"))
    op.create_index("ix_lab_templates_category","lab_templates",["category"])
    connection=op.get_bind()
    for category,names in GROUPS.items():
        connection.execute(sa.text("UPDATE lab_templates SET category=:category WHERE name = ANY(:names)"),{"category":category,"names":names})

def downgrade():
    op.drop_index("ix_lab_templates_category",table_name="lab_templates");op.drop_column("lab_templates","category")
