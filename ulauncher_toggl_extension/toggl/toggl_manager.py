import logging
from pathlib import Path
from typing import NamedTuple, Optional

from ulauncher_toggl_extension.toggl import toggl_cli as tcli

# from toggl import api, tuils


class TogglTracker(NamedTuple):
    """Tuple for holding current tracker information while executing the
    rest of the script.
    """

    entry_id: int
    workspace_id: int
    description: str


class TogglManager:
    def __init__(self, preferences: dict) -> None:
        self._config_path = Path(preferences["toggl_config_location"])
        self._maxresults: int = preferences["max_search_results"]
        self._workspace_id = preferences["project"]

    def collect_trackers(self):
        pass

    def construct_tracker(self, data: dict) -> TogglTracker:
        tracker = TogglTracker(**data)
        return tracker

    def get_workspace(self):
        pass

    def default_options(self, *args) -> dict:
        BASIC_TASKS = {"Start", "Continue", "Stop", "Goal"}
        return {}

    def continue_tracker(self, *args) -> None:
        return

    def start_tracker(self, *args) -> None:
        for i in args:
            logging.debug(i)
        return

    def add_tracker(self, *args) -> None:
        return

    def stop_tracker(self, *args) -> None:
        return

    def remove_tracker(self, *args) -> None:
        return

    def summate_trackers(self, *args) -> None:
        return

    def goal_tracker(self, *args) -> None:
        return

    def list_trackers(self, *args) -> None:
        return
