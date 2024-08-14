import pytest

from ulauncher_toggl_extension.commands.tag import (
    AddTagCommand,
    DeleteTagCommand,
    EditTagCommand,
    ListTagCommand,
    TagCommand,
)


@pytest.mark.unit
def test_tag_subcommand(dummy_ext):
    cmd = TagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration
def test_add_tag_command(dummy_ext, create_tag, helper):
    cmd = AddTagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)
    assert helper(create_tag.name, cmd) is not None


@pytest.mark.integration
def test_list_tag_command(dummy_ext):
    cmd = ListTagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration
def test_edit_tag_command(dummy_ext, helper, faker, create_tag):
    cmd = EditTagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    desc = faker.name()
    assert cmd.handle(query, model=create_tag, description=desc)
    assert helper(desc, cmd) is not None


@pytest.mark.integration
def test_delete_tag_command(dummy_ext, create_tag, helper):
    cmd = DeleteTagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)

    assert cmd.handle(query, model=create_tag)
    assert helper(create_tag.name, cmd) is None
