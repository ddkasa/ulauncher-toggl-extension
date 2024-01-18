import re
import subprocess as sp
from datetime import timedelta
from typing import TYPE_CHECKING, Final, NamedTuple, Optional

if TYPE_CHECKING:
    from ulauncher_toggl_extension.toggl.toggl_manager import TogglManager


class TogglTracker(NamedTuple):
    """Tuple for holding current tracker information while executing the
    rest of the script.
    """

    description: str
    entry_id: int
    project: str
    start: str
    duration: str
    stop: Optional[str] = None


class TogglCli:
    BASE_COMMAND: Final[str] = "toggl"
    __slots__ = ("_config_path", "_max_results", "_workspace_id", "_latest_trackers")

    def __init__(self, parent: "TogglManager") -> None:
        self._config_path = parent._config_path
        self._max_results = parent._max_results
        self._workspace_id = parent._workspace_id

        self._latest_trackers = []

    def list_trackers(self, refresh: bool = False) -> list:
        cmd = [
            self.BASE_COMMAND,
            "ls",
            "--fields",
            "description,id,project,stop",  # Toggl CLI really slow in adding additonal queries
        ]

        RIGHT_ALIGNED = {"start", "stop", "duration"}
        self._latest_trackers = []
        with sp.Popen(cmd, universal_newlines=True, bufsize=1, stdout=sp.PIPE) as shell:
            for i, line in enumerate(shell.stdout):
                if i == 0:
                    continue

                parts = re.split(r"{2,}", line.strip())
                description, duration, start, stop, entry_id, project = parts
                obj = TogglTracker(
                    entry_id=int(entry_id),
                    description=description,
                    duration=duration,
                    start=start,
                    stop=stop,
                    project=project,
                )
                self._latest_trackers.append(obj)

        # Print the result
        for item in self._latest_trackers:
            print(item)

        return self._latest_trackers

    def check_running(self) -> TogglTracker | None:
        NOT_RUNNING = "There is no time entry running!"

        cmd = ["now"]

        run = self.base_command(cmd)

        if run == NOT_RUNNING:
            return

        return

    def continue_tracker(self, *args) -> str:
        cmd = ["continue"]
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
            tag_str = tags.join(",")
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

    def base_command(self, cmd: list) -> str:
        cmd.insert(0, self.BASE_COMMAND)
        run = sp.run(cmd, capture_output=True)
        return str(run.stdout)

    def rm_tracker(self, tracker: int) -> str:
        cmd = ["rm", str(tracker)]
        return self.base_command(cmd)

    def tracker_now(self) -> str:
        cmd = ["now"]
        return self.base_command(cmd)

    def sum_tracker(self) -> str:
        cmd = ["sum"]
        return self.base_command(cmd)
