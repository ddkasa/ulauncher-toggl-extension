"""Dataclasses that hold the toggl data retrieved through the CLI.

Examples:
    >>> from ulauncher_toggl_extension.toggl.dataclasses import (
    ...     TProject,
    ...     TogglTracker,
    ... )
    >>> tracker = TogglTracker(
    ...     description="Description 1",
    ...     entry_id=1,
    ...     stop="2021-01-01 00:00:00",
    ...     project="Project 1",
    ...     start="2021-01-01 00:00:00",
    ...     duration="00:00:00",
    ...     tags=["Tag 1", "Tag 2"],
    ...     )
    >>> project = TProject(
    ...     name="Project 1",
    ...     project_id=1,
    ...     client="Client 1",
    ...     color="#000000",
    ...     )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional

from ulauncher_toggl_extension.utils import sanitize_path

from .images import CIRCULAR_SVG, SVG_CACHE

log = logging.getLogger(__name__)


@dataclass()
class TogglTracker:
    """Tracker dataclass housing single toggl tracker data.

    Methods:
        clean_tags: Sanitizes tracker tags into a list of strings.
            Called on object creation after init.
        find_color_svg: Generates path SVG colored circle file.
            SVG is generated when the project name is created.
        project_name_formatter: Generates formatted project name and id from
            provided string. Called on object creation after init.
    """

    description: str = field()
    entry_id: int = field()
    stop: str = field()
    project: str = field(default="")
    start: Optional[str] = field(default=None)
    duration: Optional[str] = field(default=None)
    tags: Optional[list[str]] = field(default=None)

    def __post_init__(self) -> None:
        if self.project and isinstance(self.project, str):
            self.project = self.project_name_formatter()
            self.project: tuple
        elif isinstance(self.project, list):
            self.project = tuple(self.project)

        self.tags = self.clean_tags()

    def clean_tags(self) -> list[str]:
        tags: list[str] = []
        if not self.tags:
            return tags

        if isinstance(self.tags, str):
            raw_tags = self.tags.split(",")
        else:
            raw_tags = self.tags.copy()

        for t in raw_tags:
            t = t.strip()
            if t:
                tags.append(t)

        return tags

    def find_color_svg(self, default: Path) -> Path:
        if not self.project or not isinstance(self.project, tuple):
            return default

        project_name = sanitize_path(self.project[0])
        img_path = SVG_CACHE / Path(f"{project_name}.svg")

        if img_path.exists():
            return img_path

        return default

    def project_name_formatter(self) -> tuple[str, int]:
        # TODO: Link to TProject object in the future and use that instead.
        # Will allow removing find color svg as the project object can provide
        # that information.
        if not self.project:
            return "No Project", 0

        try:
            project, project_id = self.project.split("(#")
        except IndexError:
            return "No Project", 0

        project = project.strip()
        return project, int(project_id[:-1])

    def __str__(self) -> str:
        return self.description


@dataclass
class TProject:
    """Project dataclass housing single toggl project data.

    Attributes:
        name(str): Project name. Sanitized project name from Toggl.
        project_id(int): Toggl project id.
        client(str): Toggl project client.
        color(str): Toggl project color in hex format.
        active(bool): Will be True most of the time as the default fetcher
            fetches all projects.

    Methods:
        generate_color_svg: Generates path SVG colored circle file.
            SVG is generated when the project is initialized.
    """

    name: str = field()  # TODO: Should sanitize in the future for quotations.
    project_id: int = field()
    client: str = field()  # TODO: Create a TogglClient object.
    color: Annotated[str, "Hex Color"] = field()
    active: bool = field(default=True)

    def __post_init__(self) -> None:
        if self.color:
            self.generate_color_svg()
        self.project_id = int(self.project_id)

    def generate_color_svg(self) -> Path:
        SVG_CACHE.mkdir(parents=True, exist_ok=True)
        name = sanitize_path(self.name)
        path = SVG_CACHE / Path(f"{name}.svg")

        if path.exists():
            return path

        log.debug("Creating SVG colored circle %s at %s.", self.color, path)
        svg = CIRCULAR_SVG.format(color=self.color)

        with path.open("w", encoding="utf-8") as file:
            file.write(svg)

        return path

    def __str__(self) -> str:
        return self.name
