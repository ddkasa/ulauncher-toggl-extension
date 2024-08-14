import os
from dataclasses import dataclass
from pathlib import Path

import pytest
from faker import Faker
from httpx import BasicAuth
from toggl_api import generate_authentication

from ulauncher_toggl_extension.date_time import get_local_tz


@pytest.fixture(autouse=True)
def _patch_noti(monkeypatch):
    def mocked_notif():
        return None

    monkeypatch.setattr(
        "ulauncher_toggl_extension.commands.meta.show_notification",
        lambda *_, **__: None,
    )


@pytest.fixture
def faker():
    return Faker()


@pytest.fixture
def auth():
    return generate_authentication()


@pytest.fixture
def get_tz():
    return get_local_tz()


@pytest.fixture
def workspace():
    return int(os.environ.get("TOGGL_WORKSPACE_ID"))


@dataclass(frozen=True)
class DummyExtension:
    """Mimics the Toggl ulauncher extension with all the required attributes."""

    auth: BasicAuth
    workspace_id: int
    cache_path: Path
    prefix: str = "tgl"
    max_results: int = 12
    hints: bool = True


@pytest.fixture
def dummy_ext(auth, workspace, tmp_path):
    return DummyExtension(auth, workspace, tmp_path)
