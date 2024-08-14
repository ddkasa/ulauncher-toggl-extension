from datetime import datetime

import pytest
from toggl_api import TogglTracker

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
def test_continue_command(dummy_ext, create_tracker):
    cmd = ContinueCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert len(cmd.preview(query)) == 0
    assert len(cmd.view(query)) == 1

    assert cmd.current_tracker().name == create_tracker.name


@pytest.mark.integration()
def test_list_command(dummy_ext):
    cmd = ListCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert isinstance(cmd.preview(query), list)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_start_command(dummy_ext, faker):
    cmd = StartCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, description=faker.name())


@pytest.mark.integration()
def test_add_command(dummy_ext, faker):
    cmd = AddCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, description=faker.name())


@pytest.mark.integration()
def test_delete_command(dummy_ext, create_tracker, helper):
    cmd = DeleteCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)

    assert cmd.handle(query, model=create_tracker)
    assert helper(create_tracker.name, cmd) is None


@pytest.mark.integration()
def test_edit_command(dummy_ext, create_tracker, faker):
    cmd = EditCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, model=create_tracker, description=faker.name())


@pytest.mark.integration()
def test_stop_command(dummy_ext, create_tracker, helper):
    cmd = StopCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert isinstance(cmd.preview(query), list)
    assert isinstance(cmd.view(query), list)

    assert cmd.handle([], model=create_tracker)
    find = helper(create_tracker.name, cmd)
    assert isinstance(find, TogglTracker)
    assert isinstance(find.stop, datetime)
