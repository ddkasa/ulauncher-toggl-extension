import time
from datetime import datetime
from pathlib import Path

import pytest
from faker import Faker
from toggl_api import JSONCache, TogglTracker, TrackerEndpoint

from ulauncher_toggl_extension.commands import (
    AddCommand,
    ContinueCommand,
    CurrentTrackerCommand,
    DeleteCommand,
    EditCommand,
    ListCommand,
    StartCommand,
    StopCommand,
)


@pytest.mark.integration
def test_continue_command(dummy_ext, create_tracker):
    cmd = ContinueCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert len(cmd.preview(query)) == 0
    assert len(cmd.view(query)) == 1

    assert cmd.current_tracker().name == create_tracker.name


@pytest.mark.integration
@pytest.mark.slow
def test_current_command(
    dummy_ext,
    create_tracker,
    auth,
    workspace,
    tmp_path,
):
    cmd = CurrentTrackerCommand(dummy_ext)
    assert cmd.get_current_tracker(refresh=True).id == create_tracker.id
    endpoint = TrackerEndpoint(workspace, auth, JSONCache(Path(tmp_path)))
    assert endpoint.stop(create_tracker).id == create_tracker.id

    time.sleep(5)

    assert cmd.get_current_tracker().id == create_tracker.id

    time.sleep(5)

    assert cmd.get_current_tracker() is None


@pytest.mark.integration
def test_list_command(dummy_ext):
    cmd = ListCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert isinstance(cmd.preview(query), list)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration
@pytest.mark.parametrize(
    "description",
    [
        r"😃",
        Faker().name(),
        r"&",
    ],
)
def test_start_command(dummy_ext, description):
    cmd = StartCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, description=description)

    cmd = CurrentTrackerCommand(dummy_ext)
    assert cmd.get_current_tracker().name == description


@pytest.mark.integration
def test_add_command(dummy_ext, faker):
    cmd = AddCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, description=faker.name())


@pytest.mark.integration
def test_delete_command(dummy_ext, create_tracker, helper):
    cmd = DeleteCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)

    assert cmd.handle(query, model=create_tracker)
    assert helper(create_tracker.name, cmd) is None


@pytest.mark.integration
def test_edit_command(dummy_ext, create_tracker, faker):
    cmd = EditCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, model=create_tracker, description=faker.name())


@pytest.mark.integration
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
