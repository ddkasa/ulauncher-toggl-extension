import pytest

from ulauncher_toggl_extension.commands import (
    AddCommand,
    ContinueCommand,
    DeleteCommand,
    EditCommand,
    ListCommand,
    StartCommand,
    StopCommand,
)


@pytest.mark.integration()
def test_continue_command(dummy_ext):
    cmd = ContinueCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration()
def test_list_command(dummy_ext):
    cmd = ListCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_start_command(dummy_ext):
    cmd = StartCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_add_command(dummy_ext):
    cmd = AddCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_delete_command(dummy_ext):
    cmd = DeleteCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_edit_command(dummy_ext):
    cmd = EditCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_stop_command(dummy_ext):
    cmd = StopCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert isinstance(cmd.preview(query), list)
    assert isinstance(cmd.view(query), list)
