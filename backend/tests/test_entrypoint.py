import os
from pathlib import Path
import shutil
import subprocess

import pytest


SH = shutil.which("sh")


@pytest.mark.skipif(SH is None, reason="POSIX shell is not available on this host")
def test_production_entrypoint_skips_migrations_and_seed(tmp_path):
    marker = tmp_path / "commands.txt"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for command in ("alembic", "python", "server"):
        executable = bin_dir / command
        executable.write_text(f'#!/bin/sh\nprintf "%s\\n" "{command}" >> "$ENTRYPOINT_MARKER"\n', encoding="utf-8")
        executable.chmod(0o755)

    env = {
        **os.environ,
        "APP_ENV": "production",
        "ENTRYPOINT_MARKER": str(marker),
        "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    entrypoint = Path(__file__).resolve().parents[1] / "entrypoint.sh"

    result = subprocess.run([SH, str(entrypoint), "server"], env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0
    assert "automatic migrations and seed commands are disabled" in result.stdout
    assert marker.read_text(encoding="utf-8").splitlines() == ["server"]
