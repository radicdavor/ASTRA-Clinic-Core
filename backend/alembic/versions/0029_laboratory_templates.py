"""Add laboratory templates.

Revision ID: 0029_laboratory_templates
Revises: 0028_laboratory_orders_results
"""
from alembic import op
import sqlalchemy as sa

revision="0029_laboratory_templates"
down_revision="0028_laboratory_orders_results"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("lab_templates",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("name",sa.String(180),nullable=False,unique=True),sa.Column("condition",sa.String(120),nullable=False),sa.Column("description",sa.Text()),sa.Column("tests",sa.JSON(),nullable=False),sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_lab_templates_name","lab_templates",["name"],unique=True);op.create_index("ix_lab_templates_condition","lab_templates",["condition"]);op.create_index("ix_lab_templates_active","lab_templates",["active"])
    op.add_column("lab_orders",sa.Column("template_id",sa.Integer(),sa.ForeignKey("lab_templates.id")))
    templates=sa.table("lab_templates",sa.column("name",sa.String),sa.column("condition",sa.String),sa.column("description",sa.Text),sa.column("tests",sa.JSON),sa.column("active",sa.Boolean))
    op.bulk_insert(templates,[
      {"name":"Debljina — prvi pregled","condition":"Debljina i metabolizam","description":"Početni laboratorijski panel prije liječničke procjene.","tests":[{"test_name":"KKS"},{"test_name":"Glukoza","unit":"mmol/L"},{"test_name":"HbA1c","unit":"%"},{"test_name":"TSH","unit":"mIU/L"},{"test_name":"ALT","unit":"U/L"},{"test_name":"AST","unit":"U/L"},{"test_name":"Kreatinin","unit":"µmol/L"},{"test_name":"Lipidogram"}],"active":True},
      {"name":"Alopecija — početna obrada","condition":"Alopecija","description":"Početni panel za liječničku obradu gubitka kose.","tests":[{"test_name":"KKS"},{"test_name":"Feritin","unit":"µg/L"},{"test_name":"Željezo","unit":"µmol/L"},{"test_name":"TSH","unit":"mIU/L"},{"test_name":"Vitamin D","unit":"nmol/L"},{"test_name":"Vitamin B12","unit":"pmol/L"},{"test_name":"Cink","unit":"µmol/L"}],"active":True}
    ])

def downgrade():
    op.drop_column("lab_orders","template_id");op.drop_table("lab_templates")
