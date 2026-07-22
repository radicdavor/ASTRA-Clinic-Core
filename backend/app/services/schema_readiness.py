from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError


RECOVERY_INCOMPLETE_TABLE = "_astra_recovery_incomplete"


@dataclass(frozen=True)
class SchemaReadiness:
    status: str
    checks: dict[str, str]
    database_revision: str | None
    expected_revision: str | None

    def to_public_dict(self) -> dict[str, object]:
        return asdict(self)


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    config = Config(str(_backend_root() / "alembic.ini"))
    config.set_main_option("script_location", str(_backend_root() / "alembic"))
    return config


def get_expected_alembic_heads(config: Config | None = None) -> tuple[str, ...]:
    if config is None:
        return _cached_expected_alembic_heads()
    script = ScriptDirectory.from_config(config)
    return tuple(script.get_heads())


def get_known_alembic_revisions(config: Config | None = None) -> frozenset[str]:
    if config is None:
        return _cached_known_alembic_revisions()
    script = ScriptDirectory.from_config(config)
    return frozenset(revision.revision for revision in script.walk_revisions())


@lru_cache(maxsize=1)
def _cached_expected_alembic_heads() -> tuple[str, ...]:
    script = ScriptDirectory.from_config(_alembic_config())
    return tuple(script.get_heads())


@lru_cache(maxsize=1)
def _cached_known_alembic_revisions() -> frozenset[str]:
    script = ScriptDirectory.from_config(_alembic_config())
    return frozenset(revision.revision for revision in script.walk_revisions())


def _database_revision_label(revisions: tuple[str, ...]) -> str | None:
    if not revisions:
        return None
    return ",".join(sorted(revisions))


def check_database_schema_readiness(
    engine: Engine,
    *,
    expected_heads_provider: Callable[[], tuple[str, ...]] = get_expected_alembic_heads,
    known_revisions_provider: Callable[[], frozenset[str]] = get_known_alembic_revisions,
) -> SchemaReadiness:
    try:
        expected_heads = expected_heads_provider()
        known_revisions = known_revisions_provider()
    except Exception:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "not_checked", "schema": "migration_metadata_unavailable"},
            database_revision=None,
            expected_revision=None,
        )

    expected_revision = _database_revision_label(expected_heads)
    if len(expected_heads) != 1:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "not_checked", "schema": "multiple_heads"},
            database_revision=None,
            expected_revision=expected_revision,
        )

    try:
        with engine.connect() as connection:
            return check_database_schema_readiness_connection(
                connection,
                expected_heads=expected_heads,
                known_revisions=known_revisions,
            )
    except SQLAlchemyError:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "unreachable", "schema": "not_checked"},
            database_revision=None,
            expected_revision=expected_revision,
        )


def check_database_schema_readiness_connection(
    connection: Connection,
    *,
    expected_heads: tuple[str, ...],
    known_revisions: frozenset[str] | None = None,
) -> SchemaReadiness:
    expected_revision = _database_revision_label(expected_heads)
    if len(expected_heads) != 1:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": "multiple_heads"},
            database_revision=None,
            expected_revision=expected_revision,
        )

    inspector = inspect(connection)
    table_names = set(inspector.get_table_names())
    if RECOVERY_INCOMPLETE_TABLE in table_names:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": "recovery_incomplete"},
            database_revision=None,
            expected_revision=expected_revision,
        )
    if "alembic_version" not in table_names:
        schema_status = "not_migrated" if not table_names else "missing_revision_table"
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": schema_status},
            database_revision=None,
            expected_revision=expected_revision,
        )

    context = MigrationContext.configure(connection)
    current_heads = tuple(context.get_current_heads())
    database_revision = _database_revision_label(current_heads)

    if not current_heads:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": "not_migrated"},
            database_revision=None,
            expected_revision=expected_revision,
        )
    if len(current_heads) != 1:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": "multiple_database_revisions"},
            database_revision=database_revision,
            expected_revision=expected_revision,
        )
    if known_revisions is not None and current_heads[0] not in known_revisions:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": "unknown_revision"},
            database_revision=database_revision,
            expected_revision=expected_revision,
        )
    if current_heads[0] != expected_heads[0]:
        return SchemaReadiness(
            status="not_ready",
            checks={"database": "reachable", "schema": "out_of_date"},
            database_revision=database_revision,
            expected_revision=expected_revision,
        )

    return SchemaReadiness(
        status="ready",
        checks={"database": "reachable", "schema": "up_to_date"},
        database_revision=database_revision,
        expected_revision=expected_revision,
    )


def check_configured_database_schema_readiness() -> SchemaReadiness:
    from app.core.database import engine

    return check_database_schema_readiness(engine)
