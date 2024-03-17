from __future__ import annotations

import enum
import logging
import subprocess as sp
from datetime import timedelta
from pathlib import Path
from typing import Optional

from ulauncher_toggl_extension.toggl.dataclasses import TogglTracker
from ulauncher_toggl_extension.utils import quote_text

from .meta import TogglCli

log = logging.getLogger(__name__)


class DateTimeType(enum.Enum):
    START = enum.auto()
    END = enum.auto()
    DURATION = enum.auto()


class TrackerCli(TogglCli):
    """Toggl tracker Cli which runs a bunch of toggl cli commands and
    processes the data.

    Holds a bunch of methods for sending commands and processing specific
        arguments.

    Noteable Methods:
        check_running(str): Checks if a tracker is currently running and
            process it into a TogglTracker object if one is running.
        continue, start, stop, delete, add, edit, now: Sends the appropriate
            TogglCli command to toggle the tracker while processing
    """

    # TODO: Needs a refactor to make the method signatures cleaner and more
    # uniform.

    __slots__ = ("latest_trackers",)

    def __init__(
        self,
        config_path: Path,
        max_results: int,
        workspace_id: Optional[int] = None,
    ) -> None:
        super().__init__(config_path, max_results, workspace_id)
        self.latest_trackers: list[TogglTracker] = []

    def fetch_objects(
        self,
        *,
        refresh: bool = False,
        **kwargs,
    ) -> list[TogglTracker]:
        """Fetches trackers from toggl and stores in a dataclass.

        Args:
            kwargs: start and stop times to filter the results by.

        Returns:
            list[TogglTracker]: List of trackers pulled from Toggl or cache.
        """
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
            log.exception("Failed to retrieve tracker list. Returning last cache.")
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
                tags=tags,  # type: ignore[arg-type]
            )
            self.latest_trackers.append(tracker)

        if refresh or not self.cache_path.exists():
            self.cache_data(self.latest_trackers)

        return self.latest_trackers

    def check_running(self) -> TogglTracker | None:
        # TODO: Refactor this method into cleaner flow.
        try:
            run = self.tracker_now()
        except sp.CalledProcessError:
            return None

        if run == "There is no time entry running!":
            return None

        lines = run.splitlines()
        try:
            desc, toggl_id = lines[0].split("#")
        except KeyError:
            desc, toggl_id = "", 0

        _, duration = lines[2].split(": ", maxsplit=1)

        try:
            _, project = lines[3].split(": ", maxsplit=1)
        except IndexError:
            project = ""

        _, start = lines[4].split(": ", maxsplit=1)

        _, tags = lines[6].split(": ", maxsplit=1)
        return TogglTracker(
            description=desc.strip(),
            entry_id=int(toggl_id),
            stop="running",
            project=project,
            start=start,
            duration=duration,
            tags=tags,  # type: ignore[arg-type]
        )

    def datetime_parameter(
        self,
        cmd: list[str],
        time: str,
        time_type: DateTimeType,
    ) -> None:
        # TODO: Pre-check datetimes in the future to prevent broken calls.
        flags = {
            DateTimeType.START: "--start",
            DateTimeType.END: "--stop",
            DateTimeType.DURATION: "--duration",
        }
        flag = flags.get(time_type)
        if flag is None:
            return
        cmd.append(flag)
        cmd.append(time)

    def continue_tracker(self, *args, **kwargs) -> str:
        cmd = ["continue"]

        if args and isinstance(args[0], TogglTracker):
            cmd.append(quote_text(args[0].description))

        start = kwargs.get("start", False)
        if start:
            self.datetime_parameter(cmd, start, DateTimeType.START)

        return self.base_command(cmd)

    def stop_tracker(self) -> str:
        cmd = ["stop"]

        try:
            run = self.base_command(cmd)
        except sp.CalledProcessError:
            log.exception("Stopping tracker unsucessful: %s")
            run = "Toggl tracker not running!"

        return run

    def add_project_parameter(
        self,
        cmd: list[str],
        project: int | str,
    ) -> None:
        cmd.append("--project")
        if isinstance(project, tuple):
            _, proj_id = project
        else:
            proj_id = project
        cmd.append(str(proj_id))

    def start_tracker(self, tracker: TogglTracker) -> str:
        cmd = ["start", quote_text(tracker.description)]

        if tracker.tags:
            cmd.append("--tags")
            tag_str = ",".join(tracker.tags)
            cmd.append(tag_str)
        if tracker.project:
            self.add_project_parameter(cmd, tracker.project)
        if tracker.start:
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
            log.exception(
                "Adding tracker with name %s was unsuccessful: %s",
                desc,
                error,  # noqa: TRY401
            )
            return f"Adding tracker with name {desc} was unsuccessful."

    def edit_tracker(self, **kwargs) -> str:
        cmd = ["now"]

        description = kwargs.get("description")
        if description is not None:
            cmd.append("--description")
            cmd.append(self.quote_text(description))

        project = kwargs.get("project")
        if project:
            self.add_project_parameter(cmd, project)

        start = kwargs.get("start")
        if start:
            cmd.append("--start")
            cmd.append(start)

        tags = kwargs.get("tags")
        if tags:
            cmd.append("--tags")
            cmd.append(tags)

        if len(cmd) == 1:
            return "No parameters to edit specified!"

        try:
            return self.base_command(cmd)
        except sp.CalledProcessError:
            log.exception("Tracker deletion error: %s")
            return "Tracker is current not running."

    def delete_tracker(self, tracker: int) -> str:
        cmd = ["rm", str(tracker)]

        try:
            return self.base_command(cmd)
        except sp.CalledProcessError:
            log.exception("Tracker deletion error: %s")
            return "Tracker with id {tracker} does not exist!"

    def tracker_now(self) -> str:
        cmd = ["now"]
        return self.base_command(cmd)

    def sum_tracker(self) -> list[tuple[str, str]]:
        """Returns basic total summation of all tracked time trackers."""
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
    def cache_len(self) -> timedelta:
        return timedelta(days=1)
