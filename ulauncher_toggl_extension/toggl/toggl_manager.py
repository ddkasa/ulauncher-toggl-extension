import logging
from functools import partial
from pathlib import Path
from types import MethodType
from typing import Callable, NamedTuple, Optional

# TODO: Integrate this instead of cli + as soon 3.12v exists for the API
## from toggl import api, tuils
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction

from ulauncher_toggl_extension.toggl import toggl_cli as tcli

START_IMG = Path("images/start.svg")
EDIT_IMG = Path("images/edit.svg")
STOP_IMG = Path("images/stop.svg")
DELETE_IMG = Path("images/delete.svg")
CONTINUE_IMG = Path("images/continue.svg")
REPORT_IMG = Path("images/report.svg")


class QueryParameters(NamedTuple):
    icon: Path
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
            CONTINUE_IMG,
            "Continue",
            "Continue the latest Toggl time tracker",
            SetUserQueryAction("tgl cnt"),
        ),
        QueryParameters(
            START_IMG,
            "Start",
            "Start a Toggl tracker",
            SetUserQueryAction("tgl stt"),
        ),
        QueryParameters(
            STOP_IMG,
            "Stop",
            "Stop the current Toggl tracker",
            SetUserQueryAction("tgl stp"),
        ),
        QueryParameters(
            START_IMG,
            "Add",
            "Add a toggl time tracker at a specified time.",
            SetUserQueryAction("tgl add"),
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

    def continue_tracker(
        self, *args
    ) -> tuple[QueryParameters, ...] | NotificationParameters:
        img = CONTINUE_IMG

        # if self.tcli.check_running() is not None:
        #     return self.default_options(*args)
        #
        # if len(args) == 1:
        #     return self.list_trackers(*args, post_method=self.continue_tracker)

        cnt = self.tcli.continue_tracker(*args)
        noti = NotificationParameters(cnt, img)

        return noti

    def start_tracker(self, *args) -> None:
        # TODO: integrate @ for a project & # for tags
        img = START_IMG

        if len(args) == 1:
            return self.list_trackers(*args, post_method=self.start_tracker)
        return

    def add_tracker(self, *args) -> None:
        img = START_IMG

        msg = self.tcli.add_tracker(args[0])

        for item in args:
            pass
        return

    def edit_tracker(self, *args) -> None:
        img = EDIT_IMG

    def stop_tracker(self, *args) -> NotificationParameters:
        img = STOP_IMG
        msg = self.tcli.stop_tracker()
        param = NotificationParameters(str(msg), img)
        return param

    def remove_tracker(self, *args) -> None:
        img = DELETE_IMG

    def summate_trackers(self, *args) -> None:
        img = REPORT_IMG

    def list_trackers(
        self, *args, post_method: Optional[MethodType] = None
    ) -> tuple[QueryParameters, ...]:
        img = REPORT_IMG
        trackers = self.tcli.list_trackers()
        return ()
