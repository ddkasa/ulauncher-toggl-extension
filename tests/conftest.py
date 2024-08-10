import os
from dataclasses import dataclass
from pathlib import Path

import pytest
from httpx import BasicAuth
from toggl_api import generate_authentication

from ulauncher_toggl_extension.date_time import get_local_tz


@pytest.fixture()
def auth():
    return generate_authentication()


@pytest.fixture()
def get_tz():
    return get_local_tz()


@pytest.fixture()
def workspace():
    return os.environ.get("TOGGL_WORKSPACE_ID")


@dataclass(frozen=True)
class DummyExtension:
    """Mimics the Toggl ulauncher extension with all the required attributes."""

    auth: BasicAuth
    workspace_id: int
    cache_path: Path
    prefix: str = "tgl"
    max_results: int = 12
    hints: bool = True


@pytest.fixture()
def dummy_ext(auth, workspace, tmp_path):
    return DummyExtension(auth, workspace, tmp_path)
