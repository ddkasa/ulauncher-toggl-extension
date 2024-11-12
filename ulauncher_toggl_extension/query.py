from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, fields
from datetime import timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, Optional, get_args

from toggl_api.reports.reports import REPORT_FORMATS

from ulauncher_toggl_extension.date_time import (
    TIME_FORMAT,
    parse_datetime,
    parse_timedelta,
)

if TYPE_CHECKING:
    from datetime import datetime, timedelta


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


class QueryParser:
    """Parser object for parsing user arguments into useable data for the extension."""

    __slots__ = ("_subcommands", "keyword", "report_format")

    MIN_ARGS: Final[int] = 2

    def __init__(
        self,
        prefix: str,
        report_format: REPORT_FORMATS,
        subcommands: frozenset[str],
    ) -> None:
        self.keyword = prefix
        self.report_format = report_format
        self._subcommands = subcommands

    def parse(self, raw_query: str) -> Query:
        """Main method that parses given arguments into a Query dataclass."""
        args = raw_query.split()
        if len(args) < self.MIN_ARGS:
            return Query(args)

        log.debug(
            "Parsing a total of %s query arguments.",
            len(args),
            extra={"query": args},
        )

        raw_data: dict[str, Any] = {
            "raw_args": args,
            "report_format": self.report_format,
            "name": self._parse_identifier(raw_query, r""),
            "id": self._parse_identifier(raw_query, r":"),
            "project": self._parse_identifier(raw_query, r"@"),
            "client": self._parse_identifier(raw_query, r"\$"),
        }

        self._parse(raw_data, *args)
        query = Query(**raw_data)

        log.info(
            "Found a total of %s arguments: %s",
            sum(1 for i in raw_data.values() if i is not None),
            query,
            extra={"raw": raw_data},
        )
        return query

    def _parse(self, raw_data: dict[str, Any], *args: str) -> None:
        quoted = False

        total = 3 if args[1] in self._subcommands else 2
        for i, arg in enumerate(args[total:], start=2):
            if not arg:
                continue

            if quoted and arg[-1] == '"':
                quoted = False
                continue

            elif not quoted and arg[0] == '"':  # noqa: RET507
                quoted = True
                continue

            if (
                i < len(args) - 1
                and (arg[0] == "<" or (arg[0] == ">" and arg[-1] != "<"))
                and args[i + 1] in TIME_FORMAT
            ):
                arg += " " + args[i + 1]

            self._parse_arg(arg, raw_data)

    def _parse_arg(self, arg: str, raw_data: dict[str, Any]) -> None:  # noqa: C901, PLR0912
        if arg == "^-":
            raw_data["sort_order"] = False

        elif (n := len(arg)) <= 1:
            return

        elif arg[0] == "#":
            raw_data["tags"] = arg[1:].split(",")

        elif arg[0] == "@" and arg[1] != '"':
            raw_data["project"] = self._parse_identifier(arg[1:])

        elif arg[0] == "$" and arg[1] != '"':
            raw_data["client"] = self._parse_identifier(arg[1:])

        elif arg[0] == "~":
            raw_data["path"] = Path.home() / Path(arg[1:].lstrip("/"))

        elif n <= 2:  # noqa: PLR2004
            return

        elif arg[0] == "." and arg[1:] in get_args(REPORT_FORMATS):
            raw_data["report_format"] = arg[1:]

        elif arg[0] == ">" and arg[-1] == "<":
            raw_data["duration"] = self._parse_timedelta(arg[1:-1])

        elif arg[0] == ">":
            raw_data["start"] = self._parse_datetime(arg[1:])

        elif arg[0] == "<":
            raw_data["stop"] = self._parse_datetime(arg[1:])

        elif arg in {"active", "private", "distinct"}:
            raw_data[arg] = False

        elif arg == "refresh":
            raw_data["refresh"] = True

        elif arg[0] == ":" and arg[1] != '"':
            raw_data["id"] = self._parse_identifier(arg[1:])

    @staticmethod
    def _parse_timedelta(timedelta: str) -> timedelta | None:
        try:
            return parse_timedelta(timedelta)
        except ValueError:
            log.warning("Invalid timedelta parsed: %s")
            return None

    @staticmethod
    def _parse_datetime(ts: str) -> datetime | None:
        try:
            return parse_datetime(ts).astimezone(timezone.utc)
        except ValueError:
            log.warning("Invalid datetime parsed: %s")
            return None

    @staticmethod
    def _parse_identifier(
        identifier: str,
        key: Optional[Literal[r"@", r"\$", r":", r""]] = None,
    ) -> str | int | None:
        if " " not in identifier:
            try:
                _id = int(identifier)
            except ValueError:
                _id = identifier
        elif isinstance(key, str):
            name_patt = r"(?P<id>(?<= " + key + r'")(.*?)+(?="))'
            name = re.search(name_patt, identifier)
            if name:
                return name.group("id")
            return None
        else:
            msg = "Identifier key is not present!"
            raise ValueError(msg)

        return _id
