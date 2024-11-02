import sys
from threading import _DummyThread
import time
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

import pytest
from faker import Faker
from toggl_api import JSONCache, TogglTag, TogglTracker, TrackerEndpoint

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
from ulauncher_toggl_extension.commands.tracker import RefreshCommand


@pytest.mark.integration
def test_continue_command(dummy_ext, create_tracker):
    cmd = ContinueCommand(dummy_ext)

    query = []
    cmd.amend_query(query)
    assert len(query) == 1

    assert len(cmd.preview(query)) == 0
    assert len(cmd.view(query)) == 1

    assert cmd.current_tracker().name == create_tracker.name

    assert cmd.handle(query)


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
    assert not cmd.preview([])
    assert not cmd.handle([])


@pytest.mark.integration
def test_current_command_stop(dummy_ext, create_tracker):
    cmd = CurrentTrackerCommand(dummy_ext)
    assert cmd.get_current_tracker(refresh=True).id == create_tracker.id
    view = cmd.view([])
    assert isinstance(view, list)
    stop_command = view[3]
    assert isinstance(stop_command.on_enter, partial)
    assert stop_command.on_enter.func == StopCommand(dummy_ext).handle
    stop_command.on_enter()
    assert cmd.tracker is None


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


@pytest.mark.unit
def test_edit_command_gen_query(dummy_ext, faker, number, workspace):
    cmd = EditCommand(dummy_ext)
    model = TogglTracker(
        number.randint(1, sys.maxsize),
        faker.name(),
        project=number.randint(1, sys.maxsize),
        workspace=workspace,
        stop=datetime.now(tz=timezone.utc),
        tags=[TogglTag(number.randint(1, sys.maxsize), faker.name())],
    )
    assert cmd.generate_query(model).startswith(
        f'{cmd.prefix} {cmd.PREFIX} "{model.name}"',
    )


@pytest.mark.unit
def test_autocomplete(dummy_ext):
    cmd = EditCommand(dummy_ext)

    assert isinstance(cmd.autocomplete(["$"]), list)

    assert isinstance(cmd.autocomplete(['"T']), list)

    assert isinstance(cmd.autocomplete(["@"]), list)

    assert isinstance(cmd.autocomplete(["#"]), list)


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


@pytest.mark.integration
def test_refresh_command(dummy_ext, create_tracker, faker):
    endpoint = TrackerEndpoint(
        dummy_ext.workspace_id,
        dummy_ext.auth,
        JSONCache(dummy_ext.cache_path),
    )
    old_name = create_tracker.name
    create_tracker.name = faker.name()
    endpoint.cache.update_entries(create_tracker)

    cmd = RefreshCommand(dummy_ext)

    assert endpoint.cache.find_entry(create_tracker).name == create_tracker.name

    cmd.handle([], model=create_tracker)

    assert endpoint.cache.find_entry(create_tracker).name == old_name
