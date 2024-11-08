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
from ulauncher_toggl_extension.query import Query


@pytest.mark.integration
def test_refresh_client_command(dummy_ext, create_client, faker, query_parser):
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
    cmd.handle(query_parser.parse("tgl client refresh"), model=create_client)

    assert endpoint.cache.find_entry(create_client).name == old_name


@pytest.mark.unit
def test_client_subcommand(dummy_ext, query_parser):
    cmd = ClientCommand(dummy_ext)

    query = query_parser.parse("tgl client")

    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration
def test_add_client_command(dummy_ext, faker, query_parser):
    cmd = AddClientCommand(dummy_ext)

    desc = faker.name()
    query = query_parser.parse(f'tgl client add "{desc}"')
    assert cmd.preview(query)
    assert cmd.view(query)

    assert cmd.handle(query)

    assert cmd.get_model(desc) is not None


@pytest.mark.integration
def test_list_client_command(dummy_ext, query_parser):
    cmd = ListClientCommand(dummy_ext)

    query = query_parser.parse("tgl client list")

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration
def test_edit_client_command(dummy_ext, create_client, faker, query_parser):
    cmd = EditClientCommand(dummy_ext)

    desc = faker.name()
    query = query_parser.parse(f'tgl client edit "{desc}"')
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, model=create_client, description=desc)

    assert cmd.get_model(desc) is not None


@pytest.mark.integration
def test_delete_client_command(dummy_ext, create_client, query_parser):
    cmd = DeleteClientCommand(dummy_ext)

    query = query_parser.parse("tgl client delete")
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, model=create_client)

    assert cmd.get_model(create_client.id) is None
