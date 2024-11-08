from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional
from dataclasses import dataclass, field, fields
from toggl_api.reports.reports import REPORT_FORMATS
from ulauncher_toggl_extension.date_time import (
    TIME_FORMAT,
)

from ulauncher_toggl_extension.date_time import parse_datetime, parse_timedelta
if TYPE_CHECKING:
    from datetime import datetime, timedelta

    from toggl_api.reports.reports import REPORT_FORMATS

log = logging.getLogger(__name__)


@dataclass
class Query:
    raw_args: list[str] = field()

    id: Optional[str | int] = field(
        default=None,
        metadata={
            "identifier": ":",
            "desc": "Identifier of a model for direct matches.",
        },
    )

    name: Optional[str] = field(
        default=None,
        metadata={
            "identifier": '"',
            "desc": "Name for editing or creating a new model.",
        },
    )

    start: Optional[datetime] = field(
        default=None,
        metadata={
            "identifier": ">",
            "desc": "Start time/date of a tracker or project.",
        },
    )

    duration: Optional[timedelta] = field(
        default=None,
        metadata={
            "identifier": ">...<",
            "desc": (
                "Duration of the tracker from the start."
                "Needs to be positive otherwise omitted."
                "Ignored if a 'stop' param imports present."
            ),
        },
    )

    stop: Optional[datetime] = field(
        default=None,
        metadata={
            "identifier": "<",
            "desc": "Stop time/date of a tracker or project.",
        },
    )

    path: Optional[Path] = field(
        default=None,
        metadata={
            "identifier": "~",
            "desc": (
                "Choose a path for where to save a report."
                "Resolves to the home directory."
            ),
        },
    )

    project: Optional[str | int] = field(
        default=None,
        metadata={
            "identifier": "project",
            "desc": "Project to use for a tracker.",
        },
    )

    client: Optional[str | int] = field(
        default=None,
        metadata={
            "identifier": "$",
            "desc": "Client to attach to a project.",
        },
    )

    tags: list[str] = field(
        default_factory=list,
        metadata={
            "identifier": "#",
            "desc": (
                "A list of tags for attaching to a tracker."
                "Use '+' to add tags and '-' to remove. Defaults to adding."
                "Also matches color argument for project."
            ),
        },
    )

    add_tags: list[str] = field(default_factory=list)
    rm_tags: list[str] = field(default_factory=list)

    report_format: REPORT_FORMATS = field(
        default="pdf",
        metadata={
            "identifier": ".",
            "desc": "File type to save a report in.",
        },
    )

    refresh: bool = field(
        default=False,
        kw_only=True,
        metadata={
            "identifier": "refresh",
            "desc": "Whether to refresh the cache from the remote Toggl API.",
        },
    )

    active: bool = field(
        default=True,
        kw_only=True,
        metadata={
            "identifier": "active",
            "desc": "Project specific flag to check if a project is not archived.",
        },
    )

    private: bool = field(
        default=False,
        kw_only=True,
        metadata={
            "identifier": "private",
            "desc": "Client specific flag to check if a client is public.",
        },
    )

    distinct: bool = field(
        default=True,
        kw_only=True,
        metadata={
            "identifier": "distinct",
            "desc": "Distinct flag for filtering model so they are unique.",
        },
    )

    sort_order: bool = field(
        default=True,
        kw_only=True,
        metadata={
            "identifier": "^-",
            "desc": "Sort direction for listing models. Defaults to descending.",
        },
    )

    def __post_init__(self) -> None:
        if self.tags:
            self._parse_tags()

        if self.stop:
            if self.start and self.stop < self.start:
                log.warning("Stop time is before start! Removing...")
                self.stop = None
        if self.stop and self.duration:
            log.warning("Stop time is present. Removing duration...")
            self.duration = None

        elif self.duration and self.duration.total_seconds() < 0:
            log.warning("Duration is negative. Removing...")
            self.duration = None

    def _parse_tags(self) -> None:
        add, remove = [], []

        for tag in self.tags:
            if tag.startswith("-"):
                remove.append(tag[1:])
            else:
                add.append(tag.removeprefix("+"))

        self.add_tags.extend(add)
        self.rm_tags.extend(remove)

    @property
    def color(self) -> str | None:
        if len(self.add_tags) == 1:
            return "#" + self.tags[0]
        return None

    @property
    def command(self) -> str | None:
        try:
            return self.raw_args[1]
        except IndexError:
            return None

    @property
    def subcommand(self) -> str | None:
        try:
            return self.raw_args[2]
        except IndexError:
            return None

    @classmethod
    def option_descriptions(cls, options: frozenset[str]) -> list[tuple[str, str]]:
        if not options:
            return []
        descriptions: list[tuple[str, str]] = []
        for f in fields(cls):
            symbol = f.metadata.get("identifier")
            if symbol in options:
                descriptions.append(
                    (
                        f.name.replace("_", " ").title(),
                        f.metadata.get("desc", ""),
                    ),
                )

        return descriptions
