import logging as log
import re
import subprocess as sp
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Final, NamedTuple, Optional

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


class TogglCli:
    BASE_COMMAND: Final[str] = "toggl"
    __slots__ = ("config_path", "max_results", "workspace_id", "latest_trackers")

    def __init__(
        self, config_path: Path, max_results: int, workspace_id: Optional[int] = None
    ) -> None:
        self.config_path = config_path
        self.max_results = max_results
        self.workspace_id = workspace_id

        self.latest_trackers = []

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, self.BASE_COMMAND)
        log.debug("Running subcommand: %s", " ".join(cmd))
        run = sp.check_output(cmd, text=True)
        return str(run)

    def list_trackers(self, refresh: bool = False) -> list[TogglTracker]:
        if not refresh:
            return self.latest_trackers

        log.info("Refreshing Toggl tracker list.")
        cmd = [
            "ls",
            "--fields",
            "description,id,stop",  # Toggl CLI really slow when looking projects
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

        if args and args[0] != "cnt":
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
