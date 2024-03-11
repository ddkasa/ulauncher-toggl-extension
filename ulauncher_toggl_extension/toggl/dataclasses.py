from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ulauncher_toggl_extension.utils import sanitize_path

from .images import CIRCULAR_SVG, SVG_CACHE

log = logging.getLogger(__name__)


@dataclass()
class TogglTracker:
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
    name: str = field()
    project_id: int = field()
    client: str = field()
    color: str = field()
    active: bool = field(default=True)

    def __post_init__(self) -> None:
        if self.color:
            self.generate_color_svg()

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
