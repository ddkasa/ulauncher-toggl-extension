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

    def list_trackers(self, refresh: bool = False) -> list[TogglTracker]:
        if not refresh:
            return self.latest_trackers

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
                continue
            # HACK/BUG: this will fail if any variable has more than 1 space within them
            desc, toggl_id, stop = re.split(r"\s{2,}", item)
            if toggl_id in checked_ids:
                continue
            checked_ids.add(toggl_id)
            cnt += 1
            tracker = TogglTracker(desc.strip(), toggl_id, stop.strip())
            self.latest_trackers.append(tracker)
            if cnt == self.max_results:
                break

        return self.latest_trackers

    def check_running(self) -> TogglTracker | None:
        NOT_RUNNING = "There is no time entry running!"

        cmd = ["now"]

        run = self.base_command(cmd)

        if run == NOT_RUNNING:
            return

        return

    def continue_tracker(self, *args) -> str:
        cmd = ["continue"]

        if len(args) == 2:
            cmd.append(args[-1])

        return self.base_command(cmd)

    def construct_tracker(self, data: dict) -> TogglTracker:
        tracker = TogglTracker(**data)
        return tracker

    def stop_tracker(self) -> str:
        cmd = ["stop"]
        return self.base_command(cmd)

    def start_tracker(
        self,
        tags: Optional[tuple[str, ...]] = None,
        project: Optional[int | str] = None,
    ) -> str:
        cmd = ["start"]
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
        start: Optional[str] = None,
        end: Optional[str] = None,
        tags: Optional[tuple[str, ...]] = None,
        project: Optional[int | str] = None,
    ) -> str:
        cmd = ["add", name]
        return self.base_command(cmd)

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, self.BASE_COMMAND)
        run = sp.check_output(cmd, text=True)
        return str(run)

    def rm_tracker(self, tracker: int) -> str:
        cmd = ["rm", str(tracker)]
        return self.base_command(cmd)

    def tracker_now(self) -> str:
        cmd = ["now"]
        return self.base_command(cmd)

    def sum_tracker(self) -> str:
        cmd = ["sum"]
        return self.base_command(cmd)
