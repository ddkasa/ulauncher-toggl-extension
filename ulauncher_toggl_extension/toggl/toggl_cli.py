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
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    pass
    # from main import TogglExtension
    # from ulauncher_toggl_extension.toggl.toggl_manager import TogglManager


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

        self._cache_path = Path(__file__).parents[2] / "cache"
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


class TrackerCli(TogglCli):
    __slots__ = "latest_trackers"

    def __init__(
        self,
        config_path: Path,
        max_results: int,
        workspace_id: Optional[int] = None,
    ) -> None:
        super().__init__(config_path, max_results, workspace_id)
        self.latest_trackers: list[TogglTracker] = []

    def list_trackers(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> list[TogglTracker]:
        start_time = kwargs.get("start", False)
        end_time = kwargs.get("stop", False)
        times = start_time or end_time

        if not refresh and self.latest_trackers and not times:
            return self.latest_trackers

        if not refresh and self.cache_path.exists() and not times:
            data = self.load_data()
            if isinstance(data, list):
                return data
            refresh = True

        log.info("Refreshing Toggl tracker list.")
        cmd = [
            "ls",
            "--fields",
            "+project,+id,+tags",
            # OPTIMIZE: Toggl CLI really slow when looking for projects
        ]
        if start_time:
            cmd.append("--start")
            cmd.append(start_time)

        if end_time:
            cmd.append("--stop")
            cmd.append(end_time)

        try:
            run = self.base_command(cmd).splitlines()
        except sp.CalledProcessError:
            log.error("Failed to retrieve tracker list. Returning last cache.")
            return self.latest_trackers

        header_size = self.count_table(run[0])
        self.latest_trackers = []
        checked_names: set[str] = set()
        cnt = 1
        for item in run:
            if cnt == 1:
                cnt += 1
                continue
            item_data = self.format_line(header_size, item, checked_names)

            if item_data is None:
                continue

            desc, dur, start, stop, project, toggl_id, tags = item_data

            checked_names.add(desc)
            cnt += 1
            tracker = TogglTracker(
                description=desc.strip(),
                entry_id=int(toggl_id),
                stop=stop.strip(),
                project=project,
                duration=dur,
                start=start,
                tags=tags.split(", "),
            )
            self.latest_trackers.append(tracker)
            if cnt == self.max_results:
                break

        if refresh or not self.cache_path.exists():
            self.cache_data(self.latest_trackers)

        return self.latest_trackers

    def check_running(self) -> TogglTracker | None:
        cmd = ["now"]

        try:
            run = self.base_command(cmd)
        except sp.CalledProcessError:
            return None

        if run == "There is no time entry running!":
            return None

        lines = run.splitlines()

        desc, toggl_id = lines[0].split("#")
        _, duration = lines[2].split(": ", maxsplit=1)
        _, project = lines[3].split(": ", maxsplit=1)
        _, start = lines[4].split(": ", maxsplit=1)

        _, tags = lines[6].split(": ", maxsplit=1)
        tracker = TogglTracker(
            description=desc.strip(),
            entry_id=int(toggl_id),
            stop="running",
            project=project,
            start=start,
            duration=duration,
            tags=tags.split(",") if tags else None,
        )

        return tracker

    def datetime_parameter(
        self, cmd: list[str], time: str, time_type: DateTimeType
    ) -> None:
        # TODO: Pre-check datetimes in the future to prevent broken calls.
        FLAGS = {
            DateTimeType.START: "--start",
            DateTimeType.END: "--stop",
            DateTimeType.DURATION: "--duration",
        }
        flag = FLAGS.get(time_type)
        if flag is None:
            return
        cmd.append(flag)
        cmd.append(time)

    def continue_tracker(self, *args, **kwargs) -> str:
        cmd = ["continue"]

        if args and isinstance(args[0], TogglTracker):
            cmd.append(self.quote_text(args[0].description))

        start = kwargs.get("start", False)
        if start:
            self.datetime_parameter(cmd, start, DateTimeType.START)

        return self.base_command(cmd)

    def stop_tracker(self) -> str:
        cmd = ["stop"]

        try:
            run = self.base_command(cmd)
        except sp.CalledProcessError as t:
            log.error("Stopping tracker unsucessful: %s", t)
            run = "Toggl tracker not running!"

        return run

    def add_project_parameter(
        self,
        cmd: list[str],
        project: int | str,
    ) -> None:
        cmd.append("--project")
        if isinstance(project, str) and "(" in project:
            _, proj_id = self.format_id_str(project)
        else:
            proj_id = project
        cmd.append(str(proj_id))

    def start_tracker(self, tracker: TogglTracker) -> str:
        cmd = ["start", self.quote_text(tracker.description)]

        if tracker.tags:
            cmd.append("--tags")
            tag_str = ",".join(tracker.tags)
            cmd.append(tag_str)
        if tracker.project is not None:
            self.add_project_parameter(cmd, tracker.project)
        if tracker.start is not None:
            self.datetime_parameter(cmd, tracker.start, DateTimeType.START)

        return self.base_command(cmd)

    def add_tracker(self, *args, **kwargs) -> str:
        start = kwargs.get("start", False)
        stop = kwargs.get("stop", False)

        if not start:
            return "Missing start date/time."
        if not stop:
            return "Missing stopping time."

        desc = args[2:3] or False
        if not isinstance(desc, str):
            return "No tracker description given."

        cmd = ["add", start, stop, self.quote_text(desc)]

        tags = kwargs.get("tags", False)
        if tags:
            cmd.append("--tags")
            cmd.append(",".join(tags))

        project = kwargs.get("project", False)
        if project:
            self.add_project_parameter(cmd, project)

        try:
            return self.base_command(cmd)
        except sp.CalledProcessError as error:
            log.error(
                "Adding tracker with name %s was unsuccessful: %s",
                desc,
                error,
            )
            return f"Adding tracker with name {desc} was unsuccessful."

    def edit_tracker(self, **kwargs) -> str:
        cmd = ["now"]

        description = kwargs.get("description")
        if description is not None:
            cmd.append("--description")
            cmd.append(self.quote_text(description))

        project = kwargs.get("project", False)
        if project:
            self.add_project_parameter(cmd, project)

        start = kwargs.get("start", False)
        if start:
            cmd.append("--start")
            cmd.append(start)

        tags = kwargs.get("tags", False)
        if tags:
            cmd.append("--tags")
            cmd.append(tags)

        if len(cmd) == 1:
            return "No parameters to edit specified!"

        try:
            return self.base_command(cmd)
        except sp.CalledProcessError as t:
            log.error("Tracker deletion error: %s", t)
            return "Tracker is current not running."

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


@dataclass
class TProject:
    name: str = field()
    project_id: int = field()
    client: str = field()
    color: str = field()
    active: bool = field(default=True)


class TogglProjects(TogglCli):
    __slots__ = ("project_list",)

    def __init__(
        self,
        config_path: Path,
        max_results: int,
        workspace_id: Optional[int] = None,
    ) -> None:
        super().__init__(config_path, max_results, workspace_id)

        self.project_list: list[TProject] = []

    def list_projects(
        self, active: bool = True, refresh: bool = False, **_
    ) -> list[TProject]:
        if not refresh and self.project_list:
            return self.project_list

        if not refresh and self.cache_path.exists():
            data = self.load_data()
            if isinstance(data, list):
                return data

        self.project_list = []

        cmd = ["ls", "-f", "+hex_color,+active"]

        run = self.base_command(cmd).splitlines()
        header_size = self.count_table(run[0])
        checked_names: set[str] = set()
        cnt = 0
        for item in run:
            if cnt == 1:
                cnt += 1
                continue
            item_data = self.format_line(header_size, item, checked_names)

            if item_data is None:
                continue

            name, client, active_item, project_id, hex_color = item_data

            active_item = True if active_item == "True" else False

            if not active_item and active:
                continue

            checked_names.add(name)
            cnt += 1
            tracker = TProject(
                name=name,
                project_id=int(project_id),
                client=client,
                color=hex_color,
                active=active_item,  # type: ignore[arg-type]
            )
            self.project_list.append(tracker)

        self.cache_data(self.project_list)

        return self.project_list

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, "projects")
        return super().base_command(cmd)

    @staticmethod
    def project_name_formatter(name: str) -> tuple[str, int]:
        name, project_id = name.split("(#")
        name = name.strip()
        return name, int(project_id[:-1])

    @property
    def cache_path(self) -> Path:
        return super().cache_path / Path("project_history.json")

    @property
    def CACHE_LEN(self) -> timedelta:
        return timedelta(weeks=2)


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
