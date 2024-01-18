import logging
from pathlib import Path
from types import MethodType
from typing import Callable, NamedTuple, Optional

# TODO: Integrate this instead of cli + as soon 3.12v exists for the API
## from toggl import api, tuils
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction

from ulauncher_toggl_extension.toggl import toggl_cli as tcli


class QueryParameters(NamedTuple):
    icon: str
    name: str
    description: str
    on_enter: Callable


class NotificationParameters(NamedTuple):
    body: str
    icon: Path
    title: str = "Toggl Extension"


class TogglManager:
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

    __slots__ = ("_config_path", "_max_results", "_workspace_id", "tcli")

    def __init__(self, preferences: dict) -> None:
        self._config_path = Path(preferences["toggl_config_location"])
        self._max_results: int = preferences["max_search_results"]
        self._workspace_id = preferences["project"]

        self.tcli = tcli.TogglCli(self)

    def collect_trackers(self):
        pass

    def default_options(self, *_) -> tuple[QueryParameters, ...]:
        return self.BASIC_TASKS

    def continue_tracker(self, *args) -> tuple[QueryParameters]:
        img = "images/continue.svg"

        if self.tcli.check_running() is not None:
            return self.default_options(*args)

        if len(args) == 1:
            return self.list_trackers(*args, post_method=self.continue_tracker)

        return ()

    def start_tracker(self, *args) -> None:
        # TODO: integrate @ for a project & # for tags
        img = "images/start.svg"

        if len(args) == 1:
            return self.list_trackers(*args, post_method=self.start_tracker)
        return

    def add_tracker(self, *args) -> None:
        img = "images/start.svg"

        for item in args:
            pass
        return

    def edit_tracker(self, *args) -> None:
        img = "images/edit.svg"

    def stop_tracker(self, *args) -> NotificationParameters:
        img = Path("images/stop.svg")
        msg = self.tcli.stop_tracker()
        param = NotificationParameters(str(msg), img)
        return param

    def remove_tracker(self, *args) -> None:
        img = "images/delete.svg"

    def summate_trackers(self, *args) -> None:
        img = "images/report.svg"

    def goal_tracker(self, *args) -> None:
        img = "images/tip.svg"

    def list_trackers(
        self, *args, post_method: Optional[MethodType] = None
    ) -> list[QueryParameters]:
        img = "images/report.svg"
        trackers = self.tcli.list_trackers()
        return ()
