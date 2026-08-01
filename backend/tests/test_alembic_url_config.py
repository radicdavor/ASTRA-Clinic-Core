from __future__ import annotations

import ast
import configparser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]


def _load_boundary_function():
    source = (ROOT / "backend" / "alembic" / "env.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "configparser_safe_url"
    )
    namespace: dict[str, object] = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "env.py", "exec"), namespace)
    return namespace["configparser_safe_url"], source


def _round_trip(url: str) -> str:
    escape, _ = _load_boundary_function()
    parser = configparser.ConfigParser()
    parser.add_section("alembic")
    parser.set("alembic", "sqlalchemy.url", escape(url))
    return parser.get("alembic", "sqlalchemy.url")


def test_alembic_url_round_trip_preserves_plain_and_percent_encoded_identity() -> None:
    plain = "postgresql+psycopg://synthetic:secret@127.0.0.1:5432/demo"
    encoded = "postgresql+psycopg://synthetic:p%40ss%3Aword@127.0.0.1:5432/demo"
    assert _round_trip(plain) == plain
    assert _round_trip(encoded) == encoded
    before = urlsplit(encoded)
    after = urlsplit(_round_trip(encoded))
    assert (after.scheme, after.hostname, after.port, after.username, after.path) == (
        before.scheme,
        before.hostname,
        before.port,
        before.username,
        before.path,
    )
    assert after.password == before.password


def test_alembic_boundary_is_local_and_does_not_log_database_url() -> None:
    escape, source = _load_boundary_function()
    encoded = "postgresql+psycopg://synthetic:p%40ss@127.0.0.1:5432/demo"
    assert escape(encoded) == encoded.replace("%", "%%")
    assert "configparser_safe_url(get_settings().database_url)" in source
    assert "print(" not in source
    assert "logger" not in source.lower()
