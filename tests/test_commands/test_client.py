import pytest

from ulauncher_toggl_extension.commands.client import (
    AddClientCommand,
    ClientCommand,
    DeleteClientCommand,
    EditClientCommand,
    ListClientCommand,
)


@pytest.mark.unit()
def test_client_subcommand(dummy_ext):
    cmd = ClientCommand(dummy_ext)

    query = []

    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration()
def test_add_client_command(dummy_ext):
    cmd = AddClientCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration()
def test_list_client_command(dummy_ext):
    cmd = ListClientCommand(dummy_ext)

    query = []

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_edit_client_command(dummy_ext):
    cmd = EditClientCommand(dummy_ext)

    query = []

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_delete_client_command(dummy_ext):
    cmd = DeleteClientCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
