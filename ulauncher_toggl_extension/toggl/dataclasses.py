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
    project: Optional[str | int] = field(default=None)
    start: Optional[str] = field(default=None)
    duration: Optional[str] = field(default=None)
    tags: Optional[list[str]] = field(default=None)


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
