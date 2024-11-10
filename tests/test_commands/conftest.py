from __future__ import annotations

from pathlib import Path

import pytest

from ulauncher_toggl_extension.commands import (
    AddClientCommand,
    AddCommand,
    AddProjectCommand,
    AddTagCommand,
    DeleteClientCommand,
    DeleteCommand,
    DeleteProjectCommand,
    DeleteTagCommand,
)
from ulauncher_toggl_extension.commands.meta import QueryResults
from ulauncher_toggl_extension.query import Query


@pytest.fixture
def create_tracker(dummy_ext, faker):
    command = AddCommand(dummy_ext)

    desc = faker.name()
    command.handle(Query([], name=desc))

    model = command.get_model(desc)
    yield model

    command = DeleteCommand(dummy_ext)
    command.handle(Query([]), model=model)


@pytest.fixture
def create_project(dummy_ext, faker):
    command = AddProjectCommand(dummy_ext)

    desc = faker.name()
    command.handle(Query([], name=desc))

    model = command.get_model(desc)
    yield model

    command = DeleteProjectCommand(dummy_ext)
    command.handle(Query([]), model=model)


@pytest.fixture
def create_client(dummy_ext, faker):
    command = AddClientCommand(dummy_ext)

    desc = faker.name()
    command.handle(Query([], name=desc))

    model = command.get_model(desc)
    yield model

    command = DeleteClientCommand(dummy_ext)
    command.handle(Query([], name=desc), model=model)


@pytest.fixture
def create_tag(dummy_ext, faker):
    command = AddTagCommand(dummy_ext)

    desc = faker.name()
    command.handle(Query([], name=desc))

    model = command.get_model(desc)
    yield model

    command = DeleteTagCommand(dummy_ext)
    command.handle(Query([]), model=model)


@pytest.fixture
def dummy_query_parameters(faker, tmp_path):
    def generate_params(total) -> list[QueryResults]:
        return [
            QueryResults(
                Path(tmp_path),
                name=faker.name(),
                description=faker.name(),
            )
            for _ in range(total)
        ]

    return generate_params
