"""Correct ambiguous legacy clinic memberships.

Revision ID: 0070_membership_correction
Revises: 0069_legacy_document_trust
"""

from alembic import op


revision = "0070_membership_correction"
down_revision = "0069_legacy_document_trust"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Earlier draft versions of 0057 could grant every clinic whose active
    # provider email matched a user case-insensitively. Preserve explicit
    # operator resolutions and system-admin scope, but fail closed for every
    # unresolved multi-clinic match.
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
        ambiguous_users AS (
            SELECT user_id
            FROM provider_candidates
            GROUP BY user_id
            HAVING count(*) > 1
        )
        DELETE FROM clinic_memberships
        USING ambiguous_users
        WHERE clinic_memberships.user_id = ambiguous_users.user_id
          AND clinic_memberships.created_by_user_id IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM clinic_membership_migration_issues
              WHERE clinic_membership_migration_issues.user_id = ambiguous_users.user_id
                AND clinic_membership_migration_issues.status = 'resolved'
          )
          AND NOT EXISTS (
              SELECT 1
              FROM users
              JOIN roles ON roles.id = users.role_id
              JOIN role_permissions ON role_permissions.role_id = roles.id
              JOIN permissions ON permissions.id = role_permissions.permission_id
              WHERE users.id = ambiguous_users.user_id
                AND permissions.name = 'system.admin'
          )
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
        ambiguous_users AS (
            SELECT
                user_id,
                json_agg(clinic_id ORDER BY clinic_id) AS candidate_clinic_ids
            FROM provider_candidates
            GROUP BY user_id
            HAVING count(*) > 1
        )
        INSERT INTO clinic_membership_migration_issues
            (user_id, reason, candidate_clinic_ids, status)
        SELECT
            ambiguous_users.user_id,
            'ambiguous_clinic_membership',
            ambiguous_users.candidate_clinic_ids,
            'pending'
        FROM ambiguous_users
        WHERE NOT EXISTS (
            SELECT 1
            FROM clinic_membership_migration_issues
            WHERE clinic_membership_migration_issues.user_id = ambiguous_users.user_id
              AND clinic_membership_migration_issues.status = 'resolved'
        )
          AND NOT EXISTS (
              SELECT 1
              FROM users
              JOIN roles ON roles.id = users.role_id
              JOIN role_permissions ON role_permissions.role_id = roles.id
              JOIN permissions ON permissions.id = role_permissions.permission_id
              WHERE users.id = ambiguous_users.user_id
                AND permissions.name = 'system.admin'
          )
        ON CONFLICT (user_id) DO UPDATE
        SET
            reason = EXCLUDED.reason,
            candidate_clinic_ids = EXCLUDED.candidate_clinic_ids,
            status = 'pending',
            resolution_clinic_id = NULL,
            resolution_note = NULL,
            resolved_at = NULL,
            resolved_by_user_id = NULL
        WHERE clinic_membership_migration_issues.status = 'pending'
        """
    )


def downgrade() -> None:
    # Removed access cannot be reconstructed safely. A downgrade intentionally
    # preserves the fail-closed correction and its operator-visible issue.
    pass
