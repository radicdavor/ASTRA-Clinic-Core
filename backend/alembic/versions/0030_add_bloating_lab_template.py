"""Add bloating laboratory template.

Revision ID: 0030_add_bloating_lab_template
Revises: 0029_laboratory_templates
"""
from alembic import op
import sqlalchemy as sa

revision = "0030_add_bloating_lab_template"
down_revision = "0029_laboratory_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO lab_templates (name, condition, description, tests, active)
        VALUES (
            'Nadutost — početna obrada',
            'Nadutost',
            'Početni panel za liječničku obradu nadutosti i povezanih probavnih tegoba.',
            CAST(:tests AS JSON),
            true
        )
        ON CONFLICT (name) DO UPDATE SET
            condition = EXCLUDED.condition,
            description = EXCLUDED.description,
            tests = EXCLUDED.tests,
            active = true,
            updated_at = now()
    """).bindparams(tests='[{"test_name":"H. pylori antigen u stolici"},{"test_name":"tTG-IgA"},{"test_name":"Ukupni IgA"},{"test_name":"Kalprotektin u stolici","unit":"µg/g"},{"test_name":"Hemokult — okultno krvarenje u stolici"}]'))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM lab_templates WHERE name = 'Nadutost — početna obrada'"))
