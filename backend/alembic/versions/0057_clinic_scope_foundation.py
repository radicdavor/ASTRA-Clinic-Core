"""Clinic scope foundation.

Revision ID: 0057_clinic_scope_foundation
Revises: 0056_reception_note_patient_concurrency
"""

from alembic import op
import sqlalchemy as sa


revision = "0057_clinic_scope_foundation"
down_revision = "0056_reception_note_patient_concurrency"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "clinic_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "clinic_id", name="uq_clinic_membership_user_clinic"),
    )
    op.create_index("ix_clinic_memberships_user_active", "clinic_memberships", ["user_id", "active"])
    op.create_index("ix_clinic_memberships_clinic_active", "clinic_memberships", ["clinic_id", "active"])

    op.create_table(
        "clinic_membership_migration_issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=80), nullable=False),
        sa.Column("candidate_clinic_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("resolution_clinic_id", sa.Integer(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("status in ('pending', 'resolved')", name="ck_clinic_membership_migration_issue_status"),
        sa.ForeignKeyConstraint(["resolution_clinic_id"], ["clinics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_clinic_membership_migration_issue_user"),
    )
    op.create_index(
        "ix_clinic_membership_migration_issues_status",
        "clinic_membership_migration_issues",
        ["status"],
    )

    op.create_table(
        "patient_clinic_associations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id", "clinic_id", name="uq_patient_clinic_association_patient_clinic"),
    )
    op.create_index("ix_patient_clinic_associations_patient_active", "patient_clinic_associations", ["patient_id", "active"])
    op.create_index("ix_patient_clinic_associations_clinic_active", "patient_clinic_associations", ["clinic_id", "active"])

    op.add_column("appointments", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_appointments_clinic_id_clinics", "appointments", "clinics", ["clinic_id"], ["id"])
    op.create_index("ix_appointments_clinic_id", "appointments", ["clinic_id"])
    op.create_index("ix_appointments_clinic_date", "appointments", ["clinic_id", "date"])

    op.add_column("patient_journeys", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_patient_journeys_clinic_id_clinics", "patient_journeys", "clinics", ["clinic_id"], ["id"])
    op.create_index("ix_patient_journeys_clinic_id", "patient_journeys", ["clinic_id"])

    op.add_column("journey_encounters", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_journey_encounters_clinic_id_clinics", "journey_encounters", "clinics", ["clinic_id"], ["id"])
    op.create_index("ix_journey_encounters_clinic_id", "journey_encounters", ["clinic_id"])

    op.add_column("clinical_documents", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_clinical_documents_clinic_id_clinics", "clinical_documents", "clinics", ["clinic_id"], ["id"])
    op.create_index("ix_clinical_documents_clinic_id", "clinical_documents", ["clinic_id"])

    op.add_column("invoices", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_invoices_clinic_id_clinics", "invoices", "clinics", ["clinic_id"], ["id"])
    op.create_index("ix_invoices_clinic_id", "invoices", ["clinic_id"])

    op.execute(
        """
        UPDATE appointments
        SET clinic_id = rooms.clinic_id
        FROM rooms
        WHERE appointments.room_id = rooms.id
          AND appointments.clinic_id IS NULL
          AND rooms.clinic_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE journey_activities
        SET clinic_id = appointments.clinic_id
        FROM appointments
        WHERE journey_activities.appointment_id = appointments.id
          AND journey_activities.clinic_id IS NULL
          AND appointments.clinic_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE patient_journeys
        SET clinic_id = appointments.clinic_id
        FROM appointments
        WHERE patient_journeys.appointment_id = appointments.id
          AND patient_journeys.clinic_id IS NULL
          AND appointments.clinic_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE patient_journeys
        SET clinic_id = activity_scope.clinic_id
        FROM (
            SELECT journey_id, min(clinic_id) AS clinic_id
            FROM journey_activities
            WHERE clinic_id IS NOT NULL
            GROUP BY journey_id
            HAVING count(DISTINCT clinic_id) = 1
        ) AS activity_scope
        WHERE patient_journeys.id = activity_scope.journey_id
          AND patient_journeys.clinic_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE journey_encounters
        SET clinic_id = patient_journeys.clinic_id
        FROM patient_journeys
        WHERE journey_encounters.journey_id = patient_journeys.id
          AND journey_encounters.clinic_id IS NULL
          AND patient_journeys.clinic_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE clinical_documents
        SET clinic_id = patient_journeys.clinic_id
        FROM patient_journeys
        WHERE clinical_documents.journey_id = patient_journeys.id
          AND clinical_documents.clinic_id IS NULL
          AND patient_journeys.clinic_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE clinical_documents
        SET clinic_id = appointments.clinic_id
        FROM appointments
        WHERE clinical_documents.appointment_id = appointments.id
          AND clinical_documents.clinic_id IS NULL
          AND appointments.clinic_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE invoices
        SET clinic_id = patient_journeys.clinic_id
        FROM patient_journeys
        WHERE invoices.journey_id = patient_journeys.id
          AND invoices.clinic_id IS NULL
          AND patient_journeys.clinic_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE invoices
        SET clinic_id = appointments.clinic_id
        FROM appointments
        WHERE invoices.appointment_id = appointments.id
          AND invoices.clinic_id IS NULL
          AND appointments.clinic_id IS NOT NULL
        """
    )

    op.execute(
        """
        INSERT INTO patient_clinic_associations (patient_id, clinic_id, active, first_seen_at, last_seen_at)
        SELECT scoped.patient_id, scoped.clinic_id, true, min(scoped.seen_at), max(scoped.seen_at)
        FROM (
            SELECT patient_id, clinic_id, created_at AS seen_at FROM appointments WHERE clinic_id IS NOT NULL
            UNION ALL
            SELECT patient_id, clinic_id, created_at AS seen_at FROM patient_journeys WHERE clinic_id IS NOT NULL
            UNION ALL
            SELECT patient_id, clinic_id, created_at AS seen_at FROM clinical_documents WHERE clinic_id IS NOT NULL
            UNION ALL
            SELECT patient_id, clinic_id, created_at AS seen_at FROM invoices WHERE clinic_id IS NOT NULL
        ) AS scoped
        WHERE NOT EXISTS (
            SELECT 1 FROM patient_clinic_associations existing
            WHERE existing.patient_id = scoped.patient_id
              AND existing.clinic_id = scoped.clinic_id
        )
        GROUP BY scoped.patient_id, scoped.clinic_id
        """
    )
    op.execute(
        """
        WITH provider_candidates AS (
            SELECT DISTINCT users.id AS user_id, providers.clinic_id
            FROM users
            JOIN providers ON lower(providers.email) = lower(users.email)
            JOIN clinics ON clinics.id = providers.clinic_id AND clinics.active = true
            WHERE users.active = true
              AND providers.active = true
              AND providers.clinic_id IS NOT NULL
        ),
        resolved_provider_scope AS (
            SELECT user_id, min(clinic_id) AS clinic_id
            FROM provider_candidates
            GROUP BY user_id
            HAVING count(*) = 1
        )
        INSERT INTO clinic_memberships (user_id, clinic_id, active)
        SELECT user_id, clinic_id, true
        FROM resolved_provider_scope
        ON CONFLICT (user_id, clinic_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO clinic_memberships (user_id, clinic_id, active)
        SELECT users.id, clinics.id, true
        FROM users
        JOIN roles ON roles.id = users.role_id
        JOIN role_permissions ON role_permissions.role_id = roles.id
        JOIN permissions ON permissions.id = role_permissions.permission_id
        CROSS JOIN clinics
        WHERE users.active = true
          AND clinics.active = true
          AND permissions.name = 'system.admin'
        ON CONFLICT (user_id, clinic_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO clinic_memberships (user_id, clinic_id, active)
        SELECT users.id, single_clinic.id, true
        FROM users
        CROSS JOIN (
            SELECT min(id) AS id
            FROM clinics
            WHERE active = true
            HAVING count(*) = 1
        ) AS single_clinic
        WHERE users.active = true
          AND NOT EXISTS (
              SELECT 1 FROM clinic_memberships
              WHERE clinic_memberships.user_id = users.id
          )
        ON CONFLICT (user_id, clinic_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO clinic_membership_migration_issues
            (user_id, reason, candidate_clinic_ids, status)
        SELECT
            users.id,
            CASE
                WHEN EXISTS (SELECT 1 FROM clinics WHERE clinics.active = true)
                THEN 'ambiguous_clinic_membership'
                ELSE 'no_active_clinic'
            END,
            COALESCE(
                (
                    SELECT json_agg(provider_candidates.clinic_id ORDER BY provider_candidates.clinic_id)
                    FROM (
                        SELECT DISTINCT providers.clinic_id
                        FROM providers
                        JOIN clinics ON clinics.id = providers.clinic_id AND clinics.active = true
                        WHERE providers.active = true
                          AND providers.clinic_id IS NOT NULL
                          AND lower(providers.email) = lower(users.email)
                    ) AS provider_candidates
                ),
                CAST('[]' AS JSON)
            ),
            'pending'
        FROM users
        WHERE users.active = true
          AND NOT EXISTS (
              SELECT 1 FROM clinic_memberships
              WHERE clinic_memberships.user_id = users.id
                AND clinic_memberships.active = true
          )
        ON CONFLICT (user_id) DO NOTHING
        """
    )


def downgrade():
    op.drop_index(
        "ix_clinic_membership_migration_issues_status",
        table_name="clinic_membership_migration_issues",
    )
    op.drop_table("clinic_membership_migration_issues")

    op.drop_index("ix_invoices_clinic_id", table_name="invoices")
    op.drop_constraint("fk_invoices_clinic_id_clinics", "invoices", type_="foreignkey")
    op.drop_column("invoices", "clinic_id")

    op.drop_index("ix_clinical_documents_clinic_id", table_name="clinical_documents")
    op.drop_constraint("fk_clinical_documents_clinic_id_clinics", "clinical_documents", type_="foreignkey")
    op.drop_column("clinical_documents", "clinic_id")

    op.drop_index("ix_journey_encounters_clinic_id", table_name="journey_encounters")
    op.drop_constraint("fk_journey_encounters_clinic_id_clinics", "journey_encounters", type_="foreignkey")
    op.drop_column("journey_encounters", "clinic_id")

    op.drop_index("ix_patient_journeys_clinic_id", table_name="patient_journeys")
    op.drop_constraint("fk_patient_journeys_clinic_id_clinics", "patient_journeys", type_="foreignkey")
    op.drop_column("patient_journeys", "clinic_id")

    op.drop_index("ix_appointments_clinic_date", table_name="appointments")
    op.drop_index("ix_appointments_clinic_id", table_name="appointments")
    op.drop_constraint("fk_appointments_clinic_id_clinics", "appointments", type_="foreignkey")
    op.drop_column("appointments", "clinic_id")

    op.drop_index("ix_patient_clinic_associations_clinic_active", table_name="patient_clinic_associations")
    op.drop_index("ix_patient_clinic_associations_patient_active", table_name="patient_clinic_associations")
    op.drop_table("patient_clinic_associations")

    op.drop_index("ix_clinic_memberships_clinic_active", table_name="clinic_memberships")
    op.drop_index("ix_clinic_memberships_user_active", table_name="clinic_memberships")
    op.drop_table("clinic_memberships")
