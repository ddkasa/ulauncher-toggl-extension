from .meta import TogglCli, TogglTracker, DateTimeType
from pathlib import Path
from typing import Optional
import logging
import subprocess as sp
from datetime import timedelta


log = logging.getLogger(__name__)


class TrackerCli(TogglCli):
    __slots__ = ("latest_trackers",)

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
        for item in run[1:]:
            item_data = self.format_line(header_size, item, checked_names)

            if item_data is None:
                continue

            desc, dur, start, stop, project, toggl_id, tags = item_data

            checked_names.add(desc)
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
        self,
        cmd: list[str],
        time: str,
        time_type: DateTimeType,
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
