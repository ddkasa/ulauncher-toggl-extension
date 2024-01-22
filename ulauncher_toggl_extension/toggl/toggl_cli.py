import json
import logging as log
import re
import subprocess as sp
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, NamedTuple, Optional

if TYPE_CHECKING:
    from main import TogglExtension


class TogglTracker(NamedTuple):
    """Tuple for holding current tracker information while executing the
    rest of the script.
    """

    description: str
    entry_id: str
    stop: str
    project: Optional[str] = None
    start: Optional[str] = None
    duration: Optional[str] = None
    tags: Optional[list[str]] = None


class TogglCli(metaclass=ABCMeta):
    BASE_COMMAND: Final[str] = "toggl"
    __slots__ = ("config_path", "max_results", "workspace_id", "_cache_path")

    def __init__(
        self, config_path: Path, max_results: int, workspace_id: Optional[int] = None
    ) -> None:
        self.config_path = config_path
        self.max_results = max_results
        self.workspace_id = workspace_id

        self._cache_path = Path(__file__).parents[2] / "cache"
        self._cache_path.mkdir(parents=True, exist_ok=True)

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, self.BASE_COMMAND)
        log.debug("Running subcommand: %s", " ".join(cmd))
        run = sp.check_output(cmd, text=True)
        return str(run)

    def count_table(self, header: str) -> list[int]:
        return []

    def cache_data(self, data: list) -> None:
        log.debug(f"Caching new data to {self.cache_path}")
        data = data.copy()
        data.append(datetime.now())
        with self.cache_path.open("w", encoding="utf-8") as file:
            file.write(json.dumps(data, cls=CustomSerializer))

    def load_data(self) -> list | None:
        log.debug(f"Loading cached data from {self.cache_path}")
        with self.cache_path.open("r", encoding="utf-8") as file:
            data = json.loads(file.read(), cls=CustomDeserializer)

        date = data.pop(0)
        if datetime.now() - self.CACHE_LEN <= date:
            return

        return data

    @property
    @abstractmethod
    def cache_path(self) -> Path:
        return self._cache_path

    @property
    @abstractmethod
    def CACHE_LEN(self) -> timedelta:
        return timedelta()


class TrackerCli(TogglCli):
    __slots__ = "latest_trackers"

    def __init__(
        self, config_path: Path, max_results: int, workspace_id: Optional[int] = None
    ) -> None:
        super().__init__(config_path, max_results, workspace_id)
        self.latest_trackers = []

    def list_trackers(self, refresh: bool = False) -> list[TogglTracker]:
        if not refresh and self.latest_trackers:
            return self.latest_trackers

        if not refresh and self.cache_path.exists():
            data = self.load_data()
            if isinstance(data, list):
                return data

        log.info("Refreshing Toggl tracker list.")
        cmd = [
            "ls",
            "--fields",
            "description,id,stop",
            # Toggl CLI really slow when looking projects
        ]
        # RIGHT_ALIGNED = {"start", "stop", "duration"}
        run = self.base_command(cmd).splitlines()
        self.latest_trackers = []
        checked_ids = set()
        cnt = 1
        for item in run:
            if cnt == 1:
                cnt += 1
                continue
            # HACK/BUG: this will fail if any variable has more than 1 space within them
            desc, toggl_id, stop = re.split(r"\s{2,}", item)
            if desc in checked_ids:
                continue
            checked_ids.add(desc)
            cnt += 1
            tracker = TogglTracker(desc.strip(), toggl_id, stop.strip())
            self.latest_trackers.append(tracker)
            if cnt == self.max_results:
                break

        self.cache_data(self.latest_trackers)

        return self.latest_trackers

    def check_running(self) -> TogglTracker | None:
        # TODO: Optimise this to use the latest list tracker call instead
        # for certain instances for more efficient usage

        cmd = ["now"]

        try:
            run = self.base_command(cmd)
        except sp.CalledProcessError:
            return

        lines = run.splitlines()

        desc, toggl_id = lines[0].split("#")
        _, duration = lines[2].split(": ", maxsplit=1)
        _, project = lines[3].split(": ", maxsplit=1)
        _, start = lines[4].split(": ", maxsplit=1)

        _, tags = lines[6].split(": ", maxsplit=1)
        tracker = TogglTracker(
            desc, toggl_id, "running", project, start, duration, tags.split(",")
        )

        return tracker

    def continue_tracker(self, *args) -> str:
        cmd = ["continue"]

        if args and args[0] not in {"continue", "cnt"}:
            cmd.append("-s")
            cmd.append(args[0])

        return self.base_command(cmd)

    def stop_tracker(self) -> str:
        cmd = ["stop"]

        try:
            run = self.base_command(cmd)
        except sp.CalledProcessError as t:
            log.error("Stopping tracker unsucessful: %s", t)
            run = "Toggl tracker not running!"

        return run

    def start_tracker(
        self,
        name: str,
        tags: Optional[tuple[str, ...]] = None,
        project: Optional[int | str] = None,
    ) -> str:
        cmd = ["start", name]
        if tags is not None:
            cmd.append("-t")
            tag_str = ",".join(tags)
            cmd.append(tag_str)
        if project is not None:
            cmd.append("-o")
            cmd.append(str(project))

        return self.base_command(cmd)

    def add_tracker(
        self,
        name: str,
        start: str,
        stop: str,
        tags: Optional[tuple[str, ...]] = None,
        project: Optional[int | str] = None,
    ) -> str:
        cmd = ["add", start, stop, name]
        if tags is not None:
            cmd.append("-t")
            cmd.append(",".join(tags))
        if project is not None:
            cmd.append("-o")
            cmd.append(str(project))

        return self.base_command(cmd)

    def rm_tracker(self, tracker: int) -> str:
        cmd = ["rm", str(tracker)]

        try:
            return self.base_command(cmd)
        except sp.CalledProcessError as t:
            log.error("Tracker deletion error: %s", t)
            return "Tracker with id {tracker} does not exist!"

    def tracker_now(self) -> str:
        cmd = ["now"]
        return self.base_command(cmd)

    def sum_tracker(self) -> list[tuple[str, str]]:
        cmd = ["sum", "-st"]

        run = self.base_command(cmd).splitlines()

        days: list[tuple[str, str]] = []
        for i, item in enumerate(run):
            if i + 1 == self.max_results:
                break
            if i == 0:
                continue
            day = item[:12].strip()
            time = item[12:].strip()
            days.append((day, time))

        return days

    @property
    def cache_path(self) -> Path:
        return super().cache_path / Path("tracker_history.json")

    @property
    def CACHE_LEN(self) -> timedelta:
        return timedelta(days=1)


class TProject(NamedTuple):
    name: str
    project_id: int
    client: str
    color: str
    active: bool = True


class TogglProjects(TogglCli):
    __slots__ = "project_list"

    def __init__(
        self, config_path: Path, max_results: int, workspace_id: Optional[int] = None
    ) -> None:
        super().__init__(config_path, max_results, workspace_id)

        self.project_list = []

    def list_projects(
        self, *args, active: bool = True, refresh: bool = False, **kwargs
    ) -> list[TProject]:
        if not refresh:
            return self.project_list

        projects = []

        cmd = ["ls", "-f", "+hex_color,+active"]

        run = self.base_command(cmd)

        return projects

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, "projects")
        return super().base_command(cmd)

    @property
    def cache_path(self) -> Path:
        return super().cache_path / Path("tracker_history.json")

    @property
    def CACHE_LEN(self) -> timedelta:
        return timedelta(weeks=1)


class CustomSerializer(json.JSONEncoder):
    def encode(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, obj: Any
    ) -> str:
        if isinstance(obj, list):
            new_obj = []
            for item in obj:
                if isinstance(item, (TProject, TogglTracker)):
                    name = type(item).__name__
                    item = item._asdict()
                    item["data type"] = name
                new_obj.append(item)

            return super().encode(new_obj)
        return super().encode(obj)

    def default(self, obj):  # pyright: ignore [reportIncompatibleMethodOverride]
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class CustomDeserializer(json.JSONDecoder):
    def decode(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, obj, **kwargs
    ) -> Any:
        obj = super().decode(obj, **kwargs)

        decoded_obj = []
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

            decoded_obj.append(item)

        return decoded_obj
