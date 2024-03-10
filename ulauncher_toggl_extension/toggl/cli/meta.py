import enum
import json
import logging
import os
import re
import subprocess as sp
from abc import ABCMeta, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from ulauncher_toggl_extension.utils import sanitize_path

from ulauncher_toggl_extension.toggl.images import (
    CACHE_PATH,
    SVG_CACHE,
    CIRCULAR_SVG,
)


log = logging.getLogger(__name__)


class DateTimeType(enum.Enum):
    START = enum.auto()
    END = enum.auto()
    DURATION = enum.auto()


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


class TogglCli(metaclass=ABCMeta):
    __slots__ = (
        "toggl_exec_path",
        "max_results",
        "workspace_id",
        "_cache_path",
    )

    def __init__(
        self,
        config_path: Path,
        max_results: int,
        workspace_id: Optional[int] = None,
    ) -> None:
        self.toggl_exec_path = str(config_path)
        self.max_results = max_results
        self.workspace_id = workspace_id

        self._cache_path = CACHE_PATH / "json"
        self._cache_path.mkdir(parents=True, exist_ok=True)

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, self.toggl_exec_path)
        tcmd = " ".join(cmd)
        log.debug("Running subcommand: %s", tcmd)

        try:
            run = sp.run(
                tcmd,
                text=True,
                env=dict(os.environ),
                shell=True,
                stdout=sp.PIPE,
                stderr=sp.PIPE,
            )
        except sp.CalledProcessError as cpe:
            log.error("'%s failed to run.'", tcmd)
            raise cpe

        return str(run.stdout.strip())

    def count_table(self, header: str) -> list[int]:
        RIGHT_ALIGNED = {"start", "stop", "duration"}

        count = []
        current_word = ""

        for index, letter in enumerate(header):
            right = current_word.strip().lower() in RIGHT_ALIGNED

            if (
                not right
                and current_word
                and current_word[-1] == " "
                and letter != " "
                and any(x.isalpha() for x in current_word)
            ):
                current_word = ""
                count.append(index + 1)

            elif right and current_word[-1] != " " and letter == " ":
                current_word = ""
                count.append(index + 1)

            current_word += letter

        return count

    def format_line(
        self,
        header_size: list[int],
        item: str,
        duplicate_names: Optional[set] = None,
    ) -> list[str] | None:
        prev = 0
        item_data = []
        for index in header_size:
            d = item[prev:index].strip()
            if isinstance(duplicate_names, set) and d in duplicate_names:
                return None
            item_data.append(d)
            prev = index
        item_data.append(item[prev:].strip())
        return item_data

    def format_id_str(self, text: str) -> tuple[str, int]:
        name, item_id = text.split("(")

        item_id = re.sub(r"[\)\(#]", "", item_id)
        name = name.strip()

        return name, int(item_id)

    def cache_data(self, data: list) -> None:
        log.debug(f"Caching new data to {self.cache_path}")
        data = data.copy()
        data.insert(0, datetime.now())
        with self.cache_path.open("w", encoding="utf-8") as file:
            file.write(json.dumps(data, cls=CustomSerializer))

    def load_data(self) -> list | None:
        log.debug(f"Loading cached data from {self.cache_path}")
        with self.cache_path.open("r", encoding="utf-8") as file:
            data = json.loads(file.read(), cls=CustomDeserializer)

        date = data.pop(0)
        if datetime.now() - self.CACHE_LEN >= date:
            log.info(
                "%s: Cache out of date. Will request new data.",
                self.__str__,
            )
            return None

        return data

    @property
    @abstractmethod
    def cache_path(self) -> Path:
        return self._cache_path

    @property
    @abstractmethod
    def CACHE_LEN(self) -> timedelta:
        return timedelta()

    def quote_text(self, text: str) -> str:
        return '"' + text + '"'


class CustomSerializer(json.JSONEncoder):
    def encode(self, obj: Any) -> str:
        if isinstance(obj, list):
            new_obj = []
            for item in obj:
                if isinstance(item, (TProject, TogglTracker)):
                    name = type(item).__name__
                    item = asdict(item)
                    item["data type"] = name
                new_obj.append(item)

            return super().encode(new_obj)
        return super().encode(obj)

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class CustomDeserializer(json.JSONDecoder):
    def decode(self, obj: Any, **kwargs) -> Any:  # type: ignore[override]
        obj = super().decode(obj, **kwargs)

        decoded_obj: list[Any] = []
        for item in obj:
            if isinstance(item, dict):
                dt = item.get("data type")
                if dt is not None:
                    item.pop("data type")
                    if dt == "TProject":
                        item = TProject(**item)
                    elif dt == "TogglTracker":
                        item = TogglTracker(**item)

            elif isinstance(item, str):
                item = datetime.fromisoformat(item)
                decoded_obj.insert(0, item)
                continue

            decoded_obj.append(item)

        return decoded_obj
