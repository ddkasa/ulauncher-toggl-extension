import pytest

from ulauncher_toggl_extension.commands.tag import (
    AddTagCommand,
    DeleteTagCommand,
    EditTagCommand,
    ListTagCommand,
    TagCommand,
)


@pytest.mark.unit
def test_tag_subcommand(dummy_ext, query_parser):
    cmd = TagCommand(dummy_ext)

    query = query_parser.parse("tgl tag")
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration
def test_add_tag_command(dummy_ext, faker, query_parser):
    cmd = AddTagCommand(dummy_ext)

    name = faker.name()
    query = query_parser.parse(f'tgl tag add "{name}"')
    assert cmd.preview(query)
    assert cmd.view(query)
    assert cmd.handle(query)
    assert cmd.get_model(name) is not None


@pytest.mark.integration
def test_list_tag_command(dummy_ext, query_parser):
    cmd = ListTagCommand(dummy_ext)

    query = query_parser.parse("tgl tag list")
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration
def test_edit_tag_command(dummy_ext, query_parser, faker, create_tag):
    cmd = EditTagCommand(dummy_ext)

    desc = faker.name()
    query = query_parser.parse(f'tgl tag edit "{desc}" :{create_tag.id} refresh')
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query)
    assert cmd.get_model(desc) is not None


@pytest.mark.integration
def test_delete_tag_command(dummy_ext, create_tag, query_parser):
    cmd = DeleteTagCommand(dummy_ext)

    query = query_parser.parse(f'tgl tag rm :"{create_tag.name}"')
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query)
    assert cmd.get_model(create_tag.name) is None
