from __future__ import annotations

import argparse
import json

import pytest

from scripts import native_dev


def args():
    return argparse.Namespace(project_name=None, compose_file=[])


def config(password="synthetic:/@ value", host="127.0.0.1", port="55432"):
    return {"services": {"db": {"environment": {
        "POSTGRES_DB": "custom_demo", "POSTGRES_USER": "custom_user",
        "POSTGRES_PASSWORD": password,
    }, "ports": [{"target": 5432, "published": port, "host_ip": host, "protocol": "tcp"}]}}}


class Result:
    def __init__(self, stdout="", returncode=0):
        self.stdout, self.returncode = stdout, returncode


def test_resolved_identity_percent_encodes_without_leaking(monkeypatch):
    monkeypatch.setattr(native_dev.subprocess, "run", lambda *a, **k: Result(json.dumps(config())))
    values, port = native_dev.resolved_identity(args())
    url = native_dev.database_url(values, "127.0.0.1", port)
    assert "custom_user" in url and "custom_demo" in url and "@127.0.0.1:55432/" in url
    assert "synthetic%3A%2F%40%20value" in url
    assert "synthetic:/@ value" not in url


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
    assert command[-6:] == ["run", "--rm", "-e", "DATABASE_URL", "backend", "true"]
    assert not any("synthetic" in item for item in command)
    assert kwargs["env"]["REAL_DATA_ALLOWED"] == "false"
