from __future__ import annotations

import argparse
import json

import pytest
from sqlalchemy.engine import make_url

from scripts import native_dev


def args():
    return argparse.Namespace(project_name=None, compose_file=[])


def config(
    password="synthetic:/@ value",
    host="127.0.0.1",
    port="55432",
    database="custom_demo",
):
    return {"services": {"db": {"environment": {
        "POSTGRES_DB": database, "POSTGRES_USER": "custom_user",
        "POSTGRES_PASSWORD": password,
    }, "ports": [{"target": 5432, "published": port, "host_ip": host, "protocol": "tcp"}]}}}


class Result:
    def __init__(self, stdout="", returncode=0):
        self.stdout, self.returncode = stdout, returncode


def test_resolved_identity_encodes_credentials_without_leaking(monkeypatch):
    monkeypatch.setattr(native_dev.subprocess, "run", lambda *a, **k: Result(json.dumps(config())))
    values, port = native_dev.resolved_identity(args())
    url = native_dev.database_url(values, "127.0.0.1", port)
    assert "custom_user" in url and "custom_demo" in url and "@127.0.0.1:55432/" in url
    assert "synthetic%3A%2F%40%20value" in url
    assert "synthetic:/@ value" not in url


@pytest.mark.parametrize(
    "database",
    (
        "astra_clinic",
        "demo clinic",
        "demo%clinic",
        "demo/clinic",
        "demo#clinic",
        "demo+clinic",
        "klinika č",
    ),
)
def test_database_url_preserves_logical_database_identity(database):
    values = config(database=database)["services"]["db"]["environment"]
    parsed = make_url(native_dev.database_url(values, "127.0.0.1", 55432))
    assert parsed.database == database
    assert parsed.username == values["POSTGRES_USER"]
    assert parsed.password == values["POSTGRES_PASSWORD"]
    assert parsed.host == "127.0.0.1"
    assert parsed.port == 55432


def test_database_url_rejects_database_query_delimiter():
    values = config(database="demo?clinic")["services"]["db"]["environment"]
    with pytest.raises(RuntimeError, match="database name cannot be represented"):
        native_dev.database_url(values, "127.0.0.1", 55432)


def test_database_url_boundary_failure_does_not_leak_credentials():
    values = config(
        database="demo?clinic", password="do-not-leak:/@%"
    )["services"]["db"]["environment"]
    with pytest.raises(RuntimeError) as captured:
        native_dev.database_url(values, "127.0.0.1", 55432)
    assert values["POSTGRES_PASSWORD"] not in str(captured.value)
    assert "postgresql" not in str(captured.value)


def test_seed_and_serve_preserve_one_logical_database_identity(monkeypatch, tmp_path):
    values = config(database="demo clinic")["services"]["db"]["environment"]
    monkeypatch.setattr(native_dev, "resolved_identity", lambda _: (values, 55432))
    monkeypatch.setattr(native_dev, "ROOT", tmp_path)
    calls = []
    monkeypatch.setattr(
        native_dev.subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)) or Result(),
    )
    assert native_dev.seed(args()) == 0
    assert native_dev.serve(args()) == 0
    seed_url = make_url(calls[0][1]["env"]["DATABASE_URL"])
    serve_url = make_url(calls[1][1]["env"]["DATABASE_URL"])
    assert seed_url.database == serve_url.database == values["POSTGRES_DB"]
    assert seed_url.username == serve_url.username == values["POSTGRES_USER"]
    assert seed_url.password == serve_url.password == values["POSTGRES_PASSWORD"]
    assert (seed_url.host, seed_url.port) == ("db", 5432)
    assert (serve_url.host, serve_url.port) == ("127.0.0.1", 55432)


@pytest.mark.parametrize("bad", (config(host="0.0.0.0"), config(host="db"), config(port=""), config(password=""), {"services": {}}))
def test_resolved_identity_rejects_unsafe_config(monkeypatch, bad):
    monkeypatch.setattr(native_dev.subprocess, "run", lambda *a, **k: Result(json.dumps(bad)))
    with pytest.raises(RuntimeError):
        native_dev.resolved_identity(args())


@pytest.mark.parametrize("host", ("remote", "db,remote", "127.0.0.1?host=remote"))
def test_database_url_rejects_target_overrides(host):
    values = {"POSTGRES_DB": "demo", "POSTGRES_USER": "user", "POSTGRES_PASSWORD": "secret"}
    with pytest.raises(RuntimeError):
        native_dev.database_url(values, host, 5432)


def test_seed_keeps_database_url_out_of_command_line(monkeypatch):
    values = config()["services"]["db"]["environment"]
    monkeypatch.setattr(native_dev, "resolved_identity", lambda _: (values, 55432))
    calls = []
    monkeypatch.setattr(native_dev.subprocess, "run", lambda command, **kwargs: calls.append((command, kwargs)) or Result())
    assert native_dev.seed(args()) == 0
    command, kwargs = calls[0]
    assert command[-7:] == ["run", "--build", "--rm", "-e", "DATABASE_URL", "backend", "true"]
    assert not any("synthetic" in item for item in command)
    assert kwargs["env"]["REAL_DATA_ALLOWED"] == "false"
    assert "--entrypoint" not in command
    assert "app.seed" not in command and "app.demo.seed" not in command


def test_seed_build_failure_is_fail_closed(monkeypatch):
    values = config()["services"]["db"]["environment"]
    monkeypatch.setattr(native_dev, "resolved_identity", lambda _: (values, 55432))
    calls = []
    monkeypatch.setattr(
        native_dev.subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)) or Result(returncode=17),
    )
    assert native_dev.seed(args()) == 17
    assert len(calls) == 1
    assert calls[0][0][-7:] == [
        "run", "--build", "--rm", "-e", "DATABASE_URL", "backend", "true"
    ]
