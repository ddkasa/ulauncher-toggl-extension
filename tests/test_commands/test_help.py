import pytest

from ulauncher_toggl_extension.commands import HelpCommand


@pytest.fixture
def help_command(dummy_ext):
    return HelpCommand(dummy_ext)


@pytest.mark.unit
def test_help_preview(help_command):
    assert help_command.preview([])


@pytest.mark.unit
def test_help_view(help_command):
    assert help_command.view([])
