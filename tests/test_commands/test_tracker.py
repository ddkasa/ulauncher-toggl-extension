import sys
import time
from datetime import datetime, timedelta, timezone
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
from ulauncher_toggl_extension.commands.project import AddProjectCommand, ProjectCommand
from ulauncher_toggl_extension.commands.tracker import RefreshCommand
from ulauncher_toggl_extension.query import Query


@pytest.mark.integration
def test_continue_command(dummy_ext, create_tracker, query_parser):
    cmd = ContinueCommand(dummy_ext)

    query = query_parser.parse("tgl continue")

    assert len(cmd.preview(query)) == 0
    assert len(cmd.view(query)) == 1

    assert cmd.current_tracker().name == create_tracker.name

    assert cmd.handle(query)


@pytest.mark.integration
@pytest.mark.slow
def test_current_command(dummy_ext, create_tracker, query_parser):
    cmd = CurrentTrackerCommand(dummy_ext)
    assert cmd.get_current_tracker(refresh=True).id == create_tracker.id
    endpoint = TrackerEndpoint(
        dummy_ext.workspace_id,
        dummy_ext.auth,
        JSONCache(Path(dummy_ext.cache_path)),
    )
    query = query_parser.parse("tgl current")
    assert endpoint.stop(create_tracker).id == create_tracker.id

    time.sleep(5)

    assert cmd.get_current_tracker().id == create_tracker.id

    time.sleep(5)

    assert cmd.get_current_tracker() is None
    assert not cmd.preview(query)
    assert not cmd.handle(query)


@pytest.mark.integration
def test_current_command_stop(dummy_ext, create_tracker, query_parser):
    cmd = CurrentTrackerCommand(dummy_ext)
    assert cmd.get_current_tracker(refresh=True).id == create_tracker.id

    query = query_parser.parse("tgl stop")
    view = cmd.view(query)
    assert isinstance(view, list)
    stop_command = view[3]
    assert isinstance(stop_command.on_enter, partial)
    assert stop_command.on_enter.func == StopCommand(dummy_ext).handle
    stop_command.on_enter()
    assert cmd.tracker is None


@pytest.mark.integration
def test_list_command(dummy_ext, query_parser):
    cmd = ListCommand(dummy_ext)

    query = query_parser.parse("tgl list")

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
def test_start_command(dummy_ext, description, query_parser):
    cmd = StartCommand(dummy_ext)

    query = query_parser.parse(f'tgl start "{description}"')

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query)

    cmd = CurrentTrackerCommand(dummy_ext)
    assert cmd.get_current_tracker().name == description


@pytest.mark.integration
def test_start_command_args(dummy_ext, query_parser, faker):
    cmd = StartCommand(dummy_ext)

    pquery = query_parser.parse(f'tgl project add "{faker.name().split()[0]}"')
    pcmd = AddProjectCommand(dummy_ext)
    assert pcmd.handle(pquery)
    pid = pcmd.get_model(pquery.name)

    name = faker.name().split()[-1]
    tag = faker.name().split()[-1]
    query = query_parser.parse(f'tgl start "{name}" @{pid.id} #{tag} refresh')

    assert cmd.handle(query)
    model = cmd.get_model(name)
    assert isinstance(model, TogglTracker)
    assert model.name == name
    assert model.project == pid.id
    assert model.tags[0].name == tag


@pytest.mark.integration
def test_add_command(dummy_ext, faker, query_parser):
    cmd = AddCommand(dummy_ext)

    name = faker.name()
    query = query_parser.parse(f'tgl add "{name}"')

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query)

    assert cmd.get_model(name) is not None


@pytest.mark.integration
def test_delete_command(dummy_ext, create_tracker, query_parser):
    cmd = DeleteCommand(dummy_ext)

    query = query_parser.parse("tgl delete")

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)

    assert cmd.handle(query, model=create_tracker)
    assert cmd.get_model(create_tracker.id) is None


@pytest.mark.integration
def test_edit_command(dummy_ext, create_tracker, faker, query_parser):
    cmd = EditCommand(dummy_ext)

    now = datetime.now().astimezone()
    stop = now + timedelta(hours=5)

    name = faker.name()
    query = query_parser.parse(
        (
            f'tgl edit :{create_tracker.id} "{name}" >{now.strftime("%H:%M")}'
            f' <{stop.strftime("%H:%M")}'
        ),
    )

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query)

    model = cmd.get_model(name)
    assert model is not None
    assert model.name == name
    start = model.start.astimezone()
    assert start.date() == now.date()
    assert start.hour == now.hour
    assert start.minute == now.minute

    comp_stop = model.stop.astimezone()
    assert comp_stop.date() == stop.date()
    assert comp_stop.hour == stop.hour
    assert comp_stop.minute == stop.minute
    assert model.duration == timedelta(hours=5)


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
@pytest.mark.parametrize("symbol", ["$", '"T', "@", "#"])
def test_autocomplete(dummy_ext, symbol, query_parser):
    cmd = EditCommand(dummy_ext)

    query = query_parser.parse("tgl edit " + symbol)

    assert isinstance(cmd.autocomplete(query), list)


@pytest.mark.integration
def test_stop_command(dummy_ext, create_tracker, query_parser):
    cmd = StopCommand(dummy_ext)

    query = query_parser.parse("tgl stop")

    assert isinstance(cmd.preview(query), list)
    assert isinstance(cmd.view(query), list)

    assert cmd.handle(query, model=create_tracker)
    find = cmd.get_model(create_tracker.name)
    assert isinstance(find, TogglTracker)
    assert isinstance(find.stop, datetime)


@pytest.mark.integration
def test_refresh_command(dummy_ext, create_tracker, faker, query_parser):
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

    cmd.handle(query_parser.parse(f"tgl refresh :{create_tracker.id}"))
    assert endpoint.cache.find_entry(create_tracker).name == old_name
