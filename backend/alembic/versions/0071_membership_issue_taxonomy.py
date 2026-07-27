"""Classify unresolved clinic membership transitions.

Revision ID: 0071_membership_taxonomy
Revises: 0070_membership_correction
"""

from alembic import op


revision = "0071_membership_taxonomy"
down_revision = "0070_membership_correction"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Compatibility for a test or review environment that already applied the
    # earlier published draft of 0070 before correction provenance was added.
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

    # The 0057 one-clinic compatibility fallback could create a null-origin
    # membership even when no active provider candidate existed. In this
    # linear migration history, a non-admin null-origin membership for a user
    # with zero active candidates is evidence of that fallback.
    op.execute(
        """
        WITH active_users AS (
            SELECT
                users.id AS user_id,
                nullif(lower(btrim(users.email)), '') AS normalized_email
            FROM users
            WHERE users.active = true
              AND NOT EXISTS (
                  SELECT 1
                  FROM roles
                  JOIN role_permissions ON role_permissions.role_id = roles.id
                  JOIN permissions ON permissions.id = role_permissions.permission_id
                  WHERE roles.id = users.role_id
                    AND permissions.name = 'system.admin'
              )
        ),
        provider_facts AS (
            SELECT
                active_users.user_id,
                active_users.normalized_email,
                count(providers.id) FILTER (
                    WHERE providers.clinic_id IS NULL
                ) AS incomplete_provider_count,
                count(providers.id) FILTER (
                    WHERE providers.active = false
                       OR clinics.active = false
                ) AS inactive_provider_count,
                count(DISTINCT providers.clinic_id) FILTER (
                    WHERE providers.active = true
                      AND clinics.active = true
                      AND providers.clinic_id IS NOT NULL
                ) AS active_candidate_count,
                COALESCE(
                    json_agg(DISTINCT providers.clinic_id ORDER BY providers.clinic_id)
                    FILTER (
                        WHERE providers.clinic_id IS NOT NULL
                          AND (providers.active = false OR clinics.active = false)
                    ),
                    CAST('[]' AS JSON)
                ) AS inactive_candidate_ids
            FROM active_users
            LEFT JOIN providers
              ON active_users.normalized_email IS NOT NULL
             AND nullif(lower(btrim(providers.email)), '') =
                 active_users.normalized_email
            LEFT JOIN clinics ON clinics.id = providers.clinic_id
            GROUP BY active_users.user_id, active_users.normalized_email
        ),
        unsupported_users AS (
            SELECT
                provider_facts.user_id,
                CASE
                    WHEN provider_facts.normalized_email IS NULL
                      OR provider_facts.incomplete_provider_count > 0
                    THEN 'invalid_provider_identity'
                    WHEN provider_facts.inactive_provider_count > 0
                    THEN 'inactive_clinic_candidate'
                    ELSE 'no_clinic_candidate'
                END AS reason,
                CASE
                    WHEN provider_facts.inactive_provider_count > 0
                    THEN provider_facts.inactive_candidate_ids
                    ELSE CAST('[]' AS JSON)
                END AS candidate_clinic_ids
            FROM provider_facts
            WHERE provider_facts.active_candidate_count = 0
        ),
        eligible_memberships AS (
            SELECT
                clinic_memberships.id,
                clinic_memberships.user_id,
                clinic_memberships.clinic_id
            FROM clinic_memberships
            JOIN unsupported_users
              ON unsupported_users.user_id = clinic_memberships.user_id
            WHERE clinic_memberships.created_by_user_id IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM clinic_membership_migration_issues
                  WHERE clinic_membership_migration_issues.user_id =
                        unsupported_users.user_id
                    AND clinic_membership_migration_issues.status = 'resolved'
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
            unsupported_users.user_id,
            unsupported_users.reason,
            unsupported_users.candidate_clinic_ids,
            'corrected_unsafe_automatic_membership',
            corrections.corrected_clinic_ids,
            'pending'
        FROM unsupported_users
        JOIN corrections ON corrections.user_id = unsupported_users.user_id
        ON CONFLICT (user_id) DO UPDATE
        SET
            reason = EXCLUDED.reason,
            candidate_clinic_ids = EXCLUDED.candidate_clinic_ids,
            correction_reason = EXCLUDED.correction_reason,
            corrected_clinic_ids = EXCLUDED.corrected_clinic_ids
        WHERE clinic_membership_migration_issues.status = 'pending'
        """
    )

    # Duplicate active provider identities for the same clinic are not a
    # unique identity signal. Remove only the automatic membership tied to
    # that duplicated candidate and record the concrete deleted clinic IDs.
    op.execute(
        """
        WITH matching_active_providers AS (
            SELECT
                users.id AS user_id,
                providers.id AS provider_id,
                providers.clinic_id
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
        duplicate_identity_users AS (
            SELECT
                user_id,
                json_agg(DISTINCT clinic_id ORDER BY clinic_id) AS candidate_clinic_ids
            FROM matching_active_providers
            GROUP BY user_id
            HAVING count(*) > count(DISTINCT clinic_id)
        ),
        eligible_memberships AS (
            SELECT
                clinic_memberships.id,
                clinic_memberships.user_id,
                clinic_memberships.clinic_id
            FROM clinic_memberships
            JOIN duplicate_identity_users
              ON duplicate_identity_users.user_id = clinic_memberships.user_id
            JOIN matching_active_providers
              ON matching_active_providers.user_id = clinic_memberships.user_id
             AND matching_active_providers.clinic_id = clinic_memberships.clinic_id
            WHERE clinic_memberships.created_by_user_id IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM clinic_membership_migration_issues
                  WHERE clinic_membership_migration_issues.user_id =
                        duplicate_identity_users.user_id
                    AND clinic_membership_migration_issues.status = 'resolved'
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM users
                  JOIN roles ON roles.id = users.role_id
                  JOIN role_permissions ON role_permissions.role_id = roles.id
                  JOIN permissions ON permissions.id = role_permissions.permission_id
                  WHERE users.id = duplicate_identity_users.user_id
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
            duplicate_identity_users.user_id,
            'invalid_provider_identity',
            duplicate_identity_users.candidate_clinic_ids,
            CASE
                WHEN corrections.user_id IS NOT NULL
                THEN 'corrected_unsafe_automatic_membership'
                ELSE NULL
            END,
            corrections.corrected_clinic_ids,
            'pending'
        FROM duplicate_identity_users
        LEFT JOIN corrections
          ON corrections.user_id = duplicate_identity_users.user_id
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
            )
        WHERE clinic_membership_migration_issues.status = 'pending'
        """
    )

    # Reclassify every unresolved transition from observable identity facts.
    # Candidate metadata contains clinic IDs only; provider e-mail values are
    # not copied into the operator-visible issue.
    op.execute(
        """
        WITH active_users AS (
            SELECT
                users.id AS user_id,
                nullif(lower(btrim(users.email)), '') AS normalized_email
            FROM users
            WHERE users.active = true
              AND NOT EXISTS (
                  SELECT 1
                  FROM roles
                  JOIN role_permissions ON role_permissions.role_id = roles.id
                  JOIN permissions ON permissions.id = role_permissions.permission_id
                  WHERE roles.id = users.role_id
                    AND permissions.name = 'system.admin'
              )
        ),
        provider_facts AS (
            SELECT
                active_users.user_id,
                active_users.normalized_email,
                count(providers.id) FILTER (
                    WHERE providers.id IS NOT NULL
                ) AS matching_provider_count,
                count(providers.id) FILTER (
                    WHERE providers.clinic_id IS NULL
                ) AS incomplete_provider_count,
                count(providers.id) FILTER (
                    WHERE providers.active = false
                       OR clinics.active = false
                ) AS inactive_provider_count,
                count(providers.id) FILTER (
                    WHERE providers.active = true
                      AND clinics.active = true
                      AND providers.clinic_id IS NOT NULL
                ) AS active_provider_count,
                count(DISTINCT providers.clinic_id) FILTER (
                    WHERE providers.active = true
                      AND clinics.active = true
                      AND providers.clinic_id IS NOT NULL
                ) AS active_candidate_count,
                COALESCE(
                    json_agg(DISTINCT providers.clinic_id ORDER BY providers.clinic_id)
                    FILTER (
                        WHERE providers.active = true
                          AND clinics.active = true
                          AND providers.clinic_id IS NOT NULL
                    ),
                    CAST('[]' AS JSON)
                ) AS active_candidate_ids,
                COALESCE(
                    json_agg(DISTINCT providers.clinic_id ORDER BY providers.clinic_id)
                    FILTER (
                        WHERE providers.clinic_id IS NOT NULL
                          AND (providers.active = false OR clinics.active = false)
                    ),
                    CAST('[]' AS JSON)
                ) AS inactive_candidate_ids
            FROM active_users
            LEFT JOIN providers
              ON active_users.normalized_email IS NOT NULL
             AND nullif(lower(btrim(providers.email)), '') =
                 active_users.normalized_email
            LEFT JOIN clinics ON clinics.id = providers.clinic_id
            GROUP BY active_users.user_id, active_users.normalized_email
        ),
        classified AS (
            SELECT
                provider_facts.user_id,
                CASE
                    WHEN provider_facts.normalized_email IS NULL
                      OR provider_facts.incomplete_provider_count > 0
                      OR provider_facts.active_provider_count >
                         provider_facts.active_candidate_count
                    THEN 'invalid_provider_identity'
                    WHEN provider_facts.active_candidate_count > 1
                    THEN 'ambiguous_active_clinic_candidates'
                    WHEN provider_facts.active_candidate_count = 0
                     AND provider_facts.inactive_provider_count > 0
                    THEN 'inactive_clinic_candidate'
                    ELSE 'no_clinic_candidate'
                END AS reason,
                CASE
                    WHEN provider_facts.active_candidate_count > 0
                    THEN provider_facts.active_candidate_ids
                    WHEN provider_facts.inactive_provider_count > 0
                    THEN provider_facts.inactive_candidate_ids
                    ELSE CAST('[]' AS JSON)
                END AS candidate_clinic_ids,
                provider_facts.active_candidate_count
            FROM provider_facts
        )
        INSERT INTO clinic_membership_migration_issues
            (user_id, reason, candidate_clinic_ids, status)
        SELECT
            classified.user_id,
            classified.reason,
            classified.candidate_clinic_ids,
            'pending'
        FROM classified
        WHERE classified.active_candidate_count <> 1
          AND NOT EXISTS (
              SELECT 1
              FROM clinic_memberships
              WHERE clinic_memberships.user_id = classified.user_id
                AND clinic_memberships.active = true
          )
        ON CONFLICT (user_id) DO UPDATE
        SET
            reason = EXCLUDED.reason,
            candidate_clinic_ids = EXCLUDED.candidate_clinic_ids
        WHERE clinic_membership_migration_issues.status = 'pending'
        """
    )


def downgrade() -> None:
    # Taxonomy and evidence of removed access remain truthful and useful after
    # a code downgrade. Re-upgrade is idempotent and never restores access.
    pass
