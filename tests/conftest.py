import pytest

from ulauncher_toggl_extension.date_time import get_local_tz


@pytest.fixture()
def get_tz():
    return get_local_tz()
