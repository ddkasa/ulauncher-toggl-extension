import subprocess  # noqa: S404
from pathlib import Path

import pytest
import tomli

from ulauncher_toggl_extension import __version__
from ulauncher_toggl_extension.utils import ensure_import


@pytest.mark.unit
def test_version():
    with (Path.cwd() / "pyproject.toml").open("rb") as pyproject:
        pyversion = tomli.load(pyproject)["tool"]["poetry"]["version"]

    assert __version__ == pyversion

    git_tag = subprocess.run(  # noqa: S603
        ["git", "describe", "--abbrev=0", "--tags"],  # noqa: S607
        stdout=subprocess.PIPE,
        check=True,
        text=True,
    ).stdout.strip()[1:]

    assert __version__ == git_tag


@pytest.mark.unit
def test_ensure_import():
    with pytest.raises((ModuleNotFoundError,)):
        ensure_import("wadwadwd", "wadwadawdw")
