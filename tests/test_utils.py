import pytest

from ulauncher_toggl_extension.utils import ensure_import


@pytest.mark.unit()
def test_ensure_import():
    with pytest.raises((ModuleNotFoundError,)):
        ensure_import("wadwadwd", "wadwadawdw")
