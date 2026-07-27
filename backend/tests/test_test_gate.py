from pathlib import Path
import runpy


GATE = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts" / "run_test_gate.py"), run_name="test_gate_module")


def test_fast_gate_is_explicit_and_excludes_postgresql_integration_directory():
    files = GATE["FAST_TESTS"]

    assert len(files) == len(set(files))
    assert all(path.startswith("tests/test_") for path in files)
    assert all("tests/integration" not in path for path in files)
    backend = Path(__file__).resolve().parents[1]
    assert all((backend / path).exists() for path in files)


def test_gate_arguments_keep_full_and_integration_layers_distinct():
    gate_arguments = GATE["gate_arguments"]

    assert gate_arguments("integration")[0] == "tests/integration"
    assert gate_arguments("full") == ["-ra", "--durations=50"]
    assert "tests/integration" not in gate_arguments("fast")


def test_full_gate_shards_cover_each_core_test_module_once():
    shards = GATE["full_core_test_shards"]()
    flattened = [path for shard in shards for path in shard]
    backend = Path(__file__).resolve().parents[1]
    expected = sorted(
        path.relative_to(backend).as_posix()
        for path in (backend / "tests").glob("test_*.py")
    )

    assert len(shards) == GATE["FULL_CORE_SHARD_COUNT"]
    assert all(shards)
    assert len(flattened) == len(set(flattened))
    assert sorted(flattened) == expected


def test_full_gate_runs_core_shards_before_postgresql_integration():
    observed = []

    assert GATE["run_full_gate"](
        ["--maxfail=1"],
        runner=lambda arguments: observed.append(arguments) or 0,
    ) == 0
    assert len(observed) == GATE["FULL_CORE_SHARD_COUNT"] + 1
    assert all("-m" in arguments and "not integration" in arguments for arguments in observed[:-1])
    assert observed[-1][:3] == ["tests/integration", "-q", "-rs"]


def test_runner_adds_backend_to_import_path_before_pytest(monkeypatch):
    backend = GATE["BACKEND"]
    observed = {}

    monkeypatch.setattr(GATE["argparse"].ArgumentParser, "parse_args", lambda _self: type("Args", (), {"gate": "fast", "pytest_args": []})())
    monkeypatch.setattr(GATE["os"], "chdir", lambda path: observed.setdefault("cwd", path))
    monkeypatch.setattr(GATE["pytest"], "main", lambda args: observed.update(args=args, sys_path=list(GATE["sys"].path)) or 0)

    assert GATE["main"]() == 0
    assert observed["cwd"] == backend
    assert observed["sys_path"][0] == str(backend)
