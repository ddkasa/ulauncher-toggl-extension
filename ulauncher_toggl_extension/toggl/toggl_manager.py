from typing import NamedTuple

from toggl import api, tuils

from ulauncher_toggl_extension.toggl import toggl_cli as tcli


class TogglTracker(NamedTuple):
    """Tuple for holding current tracker information while executing the
    rest of the script.
    """

    entry_id: int
    workspace_id: int
    description: str


class TogglManager:
    def __init__(self, workspace_id: int) -> None:
        pass

    def collect_trackers(self):
        pass

    def construct_tracker(self, data: dict) -> TogglTracker:
        tracker = TogglTracker(**data)
        return tracker

    def get_workspace(self):
        pass
