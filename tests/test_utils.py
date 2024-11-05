from pathlib import Path

import pytest
from pip._vendor import tomli  # noqa: PLC2701

from ulauncher_toggl_extension import __version__
from ulauncher_toggl_extension.utils import ensure_import


@pytest.mark.unit
def test_version():
    with (Path.cwd() / "pyproject.toml").open("rb") as pyproject:
        pyversion = tomli.load(pyproject)["tool"]["poetry"]["version"]

    assert __version__ == pyversion


@pytest.mark.unit
def test_ensure_import():
    with pytest.raises((ModuleNotFoundError,)):
        ensure_import("wadwadwd", "wadwadawdw")
