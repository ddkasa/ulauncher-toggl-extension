from __future__ import annotations

import pytest

from ulauncher_toggl_extension.commands import ListCommand
from ulauncher_toggl_extension.commands.client import ClientCommand
from ulauncher_toggl_extension.commands.help import HelpCommand
from ulauncher_toggl_extension.commands.meta import Command, SubCommand
from ulauncher_toggl_extension.commands.project import ProjectCommand
from ulauncher_toggl_extension.commands.tag import TagCommand
from ulauncher_toggl_extension.commands.tracker import TrackerCommand


@pytest.mark.unit
@pytest.mark.parametrize(
    ("data", "static"),
    [(12, 0), (1, 0), (10, 2), (15, 1), (0, 0), (200, 2)],
)
def test_cmd_paginator(data, static, dummy_ext, dummy_query_parameters):
    params = dummy_query_parameters(data)

    static_param = dummy_query_parameters(static)

    cmd = ListCommand(dummy_ext)

    total = 0
    page = 1
    per_page = dummy_ext.max_results - (static + 1)
    while total < data:
        paginator = cmd._paginator([], params, static_param, page=page)  # noqa: SLF001
        assert all(
            p.name == e.name and p.description == e.description
            for p, e in zip(paginator[:per_page], params[per_page * page : per_page])
        )
        total += min(per_page, len(paginator))
        page += 1

    assert total == data


def parse_prefix(commands: list[type[Command]]) -> bool:
    data = set()
    for c in commands:
        if not c.PREFIX:
            continue
        if c.PREFIX in data:
            return False
        data.add(c.PREFIX)

        if not c.ALIASES:
            continue

        for x in c.ALIASES:
            if x in data:
                return False
            data.add(x)

    return True


@pytest.mark.unit
def test_cmd_collisions():
    commands = (
        Command.__subclasses__()
        + SubCommand.__subclasses__()
        + TrackerCommand.__subclasses__()
    )
    commands.remove(SubCommand)

    assert parse_prefix(commands)

    assert parse_prefix(ProjectCommand.__subclasses__())

    assert parse_prefix(TagCommand.__subclasses__())

    assert parse_prefix(ClientCommand.__subclasses__())

    assert parse_prefix(HelpCommand.__subclasses__())
