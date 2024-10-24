import os
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from random import Random

import pytest
from faker import Faker
from httpx import BasicAuth
from toggl_api import generate_authentication
from toggl_api.reports.reports import REPORT_FORMATS

from ulauncher_toggl_extension.date_time import get_local_tz


@pytest.fixture(autouse=True)
def _rate_limit(request):
    yield
    if "integration" in request.keywords:
        time.sleep(1)


@pytest.fixture(autouse=True)
def _patch_noti(monkeypatch):
    def mocked_notif():
        return None

    monkeypatch.setattr(
        "ulauncher_toggl_extension.commands.meta.show_notification",
        lambda *_, **__: None,
    )


@pytest.fixture
def number():
    return Random()  # noqa: S311


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
    report_format: REPORT_FORMATS = "csv"
    expiration: timedelta = timedelta(days=7)


@pytest.fixture
def dummy_ext(auth, workspace, tmp_path):
    return DummyExtension(auth, workspace, tmp_path)
