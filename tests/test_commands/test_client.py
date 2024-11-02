import pytest
from toggl_api import ClientEndpoint, JSONCache

from ulauncher_toggl_extension.commands.client import (
    AddClientCommand,
    ClientCommand,
    DeleteClientCommand,
    EditClientCommand,
    ListClientCommand,
    RefreshClientCommand,
)


@pytest.mark.integration
def test_refresh_client_command(dummy_ext, create_client, faker):
    endpoint = ClientEndpoint(
        dummy_ext.workspace_id,
        dummy_ext.auth,
        JSONCache(dummy_ext.cache_path),
    )
    old_name = create_client.name
    create_client.name = faker.name()
    endpoint.cache.update_entries(create_client)

    assert endpoint.cache.find_entry(create_client).name == create_client.name

    cmd = RefreshClientCommand(dummy_ext)
    cmd.handle([], model=create_client)

    assert endpoint.cache.find_entry(create_client).name == old_name


@pytest.mark.unit
def test_client_subcommand(dummy_ext):
    cmd = ClientCommand(dummy_ext)

    query = []

    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration
def test_add_client_command(dummy_ext, faker, helper):
    cmd = AddClientCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)

    desc = faker.name()
    assert cmd.handle(query, description=desc)

    assert helper(desc, cmd) is not None


@pytest.mark.integration
def test_list_client_command(dummy_ext):
    cmd = ListClientCommand(dummy_ext)

    query = []

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration
def test_edit_client_command(dummy_ext, create_client, faker, helper):
    cmd = EditClientCommand(dummy_ext)

    query = []

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    desc = faker.name()
    assert cmd.handle(query, model=create_client, description=desc)

    assert helper(desc, cmd) is not None


@pytest.mark.integration
def test_delete_client_command(dummy_ext, create_client):
    cmd = DeleteClientCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, model=create_client)
