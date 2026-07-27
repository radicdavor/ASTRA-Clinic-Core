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
    # The correction must be recorded in the same transaction as the delete:
    # after this revision there is no reliable way to infer whether an
    # ambiguous user actually had an unsafe membership or merely had no scope.
    # IF NOT EXISTS keeps the intentionally fail-closed no-op downgrade
    # re-upgrade safe for this PostgreSQL-only migration.
    op.execute(
        """
        ALTER TABLE clinic_membership_migration_issues
        ADD COLUMN IF NOT EXISTS correction_reason VARCHAR(80)
        """
    )
    op.execute(
        """
        ALTER TABLE clinic_membership_migration_issues
        ADD COLUMN IF NOT EXISTS corrected_clinic_ids JSON
        """
    )
    # Earlier draft versions of 0057 could grant every clinic whose active
    # provider email matched a user case-insensitively. Preserve explicit
    # operator resolutions, unrelated scope, and system-admin scope. Only an
    # automatic membership to an actual ambiguous provider candidate is
    # evidence-bound enough to remove.
    op.execute(
        """
        WITH provider_candidates AS (
            SELECT DISTINCT users.id AS user_id, providers.clinic_id
            FROM users
            JOIN providers
              ON lower(btrim(providers.email)) = lower(btrim(users.email))
            JOIN clinics ON clinics.id = providers.clinic_id AND clinics.active = true
            WHERE users.active = true
              AND providers.active = true
              AND providers.clinic_id IS NOT NULL
              AND nullif(btrim(users.email), '') IS NOT NULL
              AND nullif(btrim(providers.email), '') IS NOT NULL
        ),
        ambiguous_users AS (
            SELECT
                user_id,
                json_agg(clinic_id ORDER BY clinic_id) AS candidate_clinic_ids
            FROM provider_candidates
            GROUP BY user_id
            HAVING count(*) > 1
        ),
        eligible_memberships AS (
            SELECT
                clinic_memberships.id,
                clinic_memberships.user_id,
                clinic_memberships.clinic_id
            FROM clinic_memberships
            JOIN ambiguous_users
              ON ambiguous_users.user_id = clinic_memberships.user_id
            JOIN provider_candidates
              ON provider_candidates.user_id = clinic_memberships.user_id
             AND provider_candidates.clinic_id = clinic_memberships.clinic_id
            WHERE clinic_memberships.created_by_user_id IS NULL
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
        ),
        deleted_memberships AS (
            DELETE FROM clinic_memberships
            USING eligible_memberships
            WHERE clinic_memberships.id = eligible_memberships.id
            RETURNING
                clinic_memberships.user_id,
                clinic_memberships.clinic_id
        ),
        corrections AS (
            SELECT
                user_id,
                json_agg(clinic_id ORDER BY clinic_id) AS corrected_clinic_ids
            FROM deleted_memberships
            GROUP BY user_id
        )
        INSERT INTO clinic_membership_migration_issues
            (
                user_id,
                reason,
                candidate_clinic_ids,
                correction_reason,
                corrected_clinic_ids,
                status
            )
        SELECT
            ambiguous_users.user_id,
            'ambiguous_active_clinic_candidates',
            ambiguous_users.candidate_clinic_ids,
            CASE
                WHEN corrections.user_id IS NOT NULL
                THEN 'corrected_unsafe_automatic_membership'
                ELSE NULL
            END,
            corrections.corrected_clinic_ids,
            'pending'
        FROM ambiguous_users
        LEFT JOIN corrections ON corrections.user_id = ambiguous_users.user_id
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
            correction_reason = COALESCE(
                EXCLUDED.correction_reason,
                clinic_membership_migration_issues.correction_reason
            ),
            corrected_clinic_ids = COALESCE(
                EXCLUDED.corrected_clinic_ids,
                clinic_membership_migration_issues.corrected_clinic_ids
            ),
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
