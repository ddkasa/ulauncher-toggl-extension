import pytest

from ulauncher_toggl_extension.commands.tag import (
    AddTagCommand,
    DeleteTagCommand,
    EditTagCommand,
    ListTagCommand,
    TagCommand,
)


@pytest.mark.unit()
def test_tag_subcommand(dummy_ext):
    cmd = TagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration()
def test_add_tag_command(dummy_ext):
    cmd = AddTagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration()
def test_list_tag_command(dummy_ext):
    cmd = ListTagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_edit_tag_command(dummy_ext):
    cmd = EditTagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_delete_tag_command(dummy_ext):
    cmd = DeleteTagCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
