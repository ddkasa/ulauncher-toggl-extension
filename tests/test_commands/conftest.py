from __future__ import annotations

from typing import TYPE_CHECKING

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
from ulauncher_toggl_extension.commands.meta import Command

if TYPE_CHECKING:
    from toggl_api.modules.models import TogglClass


def _find_model(name: str, cmd: Command | list) -> TogglClass | None:
    models = cmd.get_models() if isinstance(cmd, Command) else cmd

    for model in models:
        if name == model.name:
            return model

    return None


@pytest.fixture(scope="session")
def helper():
    return _find_model


@pytest.fixture
def create_tracker(dummy_ext, faker):
    command = AddCommand(dummy_ext)

    desc = faker.name()
    command.handle([], description=desc)

    model = _find_model(desc, command)
    yield model

    command = DeleteCommand(dummy_ext)
    command.handle([], model=model)


@pytest.fixture
def create_project(dummy_ext, faker):
    command = AddProjectCommand(dummy_ext)

    desc = faker.name()
    command.handle([], description=desc)

    model = _find_model(desc, command)
    yield model

    command = DeleteProjectCommand(dummy_ext)
    command.handle([], model=model)


@pytest.fixture
def create_client(dummy_ext, faker):
    command = AddClientCommand(dummy_ext)

    desc = faker.name()
    command.handle([], description=desc)

    model = _find_model(desc, command)
    yield model

    command = DeleteClientCommand(dummy_ext)
    command.handle([], model=model)


@pytest.fixture
def create_tag(dummy_ext, faker):
    command = AddTagCommand(dummy_ext)

    desc = faker.name()
    command.handle([], description=desc)

    model = _find_model(desc, command)
    yield model

    command = DeleteTagCommand(dummy_ext)
    command.handle([], model=model)
