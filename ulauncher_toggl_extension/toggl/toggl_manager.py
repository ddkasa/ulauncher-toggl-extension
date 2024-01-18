import logging
from functools import cache
from pathlib import Path
from typing import Callable, NamedTuple

from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from ulauncher_toggl_extension.toggl import toggl_cli as tcli

# from toggl import api, tuils


class TogglTracker(NamedTuple):
    """Tuple for holding current tracker information while executing the
    rest of the script.
    """

    entry_id: int
    workspace_id: int
    description: str


class QueryParameters(NamedTuple):
    icon: str
    name: str
    description: str
    on_enter: Callable


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

    @cache
    def default_options(self, *_) -> tuple[QueryParameters, ...]:
        BASIC_TASKS = (
            QueryParameters(
                "images/continue.svg",
                "Continue",
                "Continue the latest Toggl time tracker",
                SetUserQueryAction("tgl cnt"),
            ),
            QueryParameters(
                "images/tip.svg",
                "Goal Tracker",
                "Start a Toggl tracker with a goal duration.",
                SetUserQueryAction("tgl gl"),
            ),
            QueryParameters(
                "images/start.svg",
                "Start",
                "Start a Toggl tracker",
                SetUserQueryAction("tgl stt"),
            ),
            QueryParameters(
                "images/stop.svg",
                "Stop",
                "Stop the current Toggl tracker",
                SetUserQueryAction("tgl stp"),
            ),
        )

        return BASIC_TASKS

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
