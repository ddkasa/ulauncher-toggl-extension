import logging as log
from functools import cache, partial
from pathlib import Path
from types import MethodType
from typing import Callable, NamedTuple, Optional

from gi.repository import Notify
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

# TODO: Integrate this instead of cli + as soon 3.12v exists for the API
## from toggl import api, tuils
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction

from ulauncher_toggl_extension.toggl import toggl_cli as tcli

START_IMG = Path("images/start.svg")
EDIT_IMG = Path("images/edit.svg")
ADD_IMG = Path("images/add.svg")  # TODO: Needs to be created.
STOP_IMG = Path("images/stop.svg")
DELETE_IMG = Path("images/delete.svg")
CONTINUE_IMG = Path("images/continue.svg")
REPORT_IMG = Path("images/reports.svg")
BROWSER_IMG = Path("images/browser.svg")


class QueryParameters(NamedTuple):
    icon: Path
    name: str
    description: str
    on_enter: BaseAction
    on_alt_enter: Optional[BaseAction] = None


class NotificationParameters(NamedTuple):
    body: str
    icon: Path
    title: str = "Toggl Extension"


class TogglViewer:
    __slots__ = ("_config_path", "_max_results", "_workspace_id", "tcli", "manager")

    def __init__(self, preferences: dict) -> None:
        self._config_path = Path(preferences["toggl_config_location"])
        self._max_results: int = preferences["max_search_results"]
        self._workspace_id = preferences["project"]

        self.tcli = tcli.TogglCli(self)
        self.manager = TogglManager(preferences)

    @cache
    def default_options(self, *_) -> tuple[QueryParameters, ...]:
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
            QueryParameters(
                DELETE_IMG,
                "Delete",
                "Delete a Toggl time tracker",
                SetUserQueryAction("tgl rm"),
            ),
            QueryParameters(
                REPORT_IMG,
                "Report",
                "View a report of previous week of trackers.",
                ExtensionCustomAction(
                    partial(self.manager.total_trackers), keep_app_open=True
                ),
            ),
            QueryParameters(
                BROWSER_IMG,
                "List",
                f"View the last {self._max_results} trackers.",
                ExtensionCustomAction(
                    partial(self.manager.total_trackers), keep_app_open=True
                ),
            ),
        )
        return BASIC_TASKS

    def continue_tracker(self, *args) -> list[QueryParameters]:
        img = CONTINUE_IMG

        base_param = QueryParameters(
            img,
            "Continue",
            "Continue the last tracker.",
            ExtensionCustomAction(
                partial(self.manager.continue_tracker, *args),
                keep_app_open=False,
            ),
        )

        return [base_param]

    def start_tracker(self, *args) -> list[QueryParameters]:
        # TODO: integrate @ for a project & # for tags
        img = START_IMG

        base_param = QueryParameters(
            img,
            "Start",
            "Start a new tracker.",
            ExtensionCustomAction(
                partial(self.manager.start_tracker, *args),
                keep_app_open=False,
            ),
        )

        return [base_param]

    def add_tracker(self, *args) -> list[QueryParameters]:
        img = EDIT_IMG
        base_param = QueryParameters(
            img,
            "Add",
            "Add a new tracker.",
            ExtensionCustomAction(
                partial(self.manager.add_tracker, *args),
                keep_app_open=True,
            ),
        )

        return [base_param]

    def edit_tracker(self, *args) -> list[QueryParameters]:
        img = EDIT_IMG
        params = QueryParameters(
            img,
            "Edit",
            "Edit a tracker.",
            ExtensionCustomAction(
                partial(self.manager.edit_tracker, *args), keep_app_ope=True
            ),
        )
        return [params]

    def stop_tracker(self, *args) -> list[QueryParameters]:
        img = STOP_IMG
        params = QueryParameters(
            img,
            "Stop",
            "Stop the current tracker.",
            ExtensionCustomAction(
                partial(self.manager.stop_tracker, *args),
                keep_app_open=False,
            ),
        )
        return [params]

    def remove_tracker(self, *args) -> list[QueryParameters]:
        img = DELETE_IMG
        params = QueryParameters(
            img,
            "Delete",
            "Delete tracker.",
            ExtensionCustomAction(
                partial(self.manager.remove_tracker, *args),
                keep_app_open=False,
            ),
        )
        return [params]

    def total_trackers(self, *args) -> list[QueryParameters]:
        img = REPORT_IMG

        params = QueryParameters(
            img,
            "Generate Report",
            "View a weekly total of your trackers.",
            ExtensionCustomAction(
                partial(self.manager.total_trackers, *args), keep_app_open=True
            ),
        )
        return [params]

    def list_trackers(
        self, *args, post_method: Optional[MethodType] = None
    ) -> list[QueryParameters]:
        img = BROWSER_IMG
        params = QueryParameters(
            img,
            "List",
            f"View the last {self._max_results} trackers.",
            ExtensionCustomAction(
                partial(self.manager.list_trackers, *args), keep_app_open=True
            ),
        )
        return [params]


class TogglManager:
    __slots__ = (
        "_config_path",
        "_max_results",
        "_workspace_id",
        "tcli",
        "notification",
    )

    def __init__(self, preferences: dict) -> None:
        self._config_path = Path(preferences["toggl_config_location"])
        self._max_results: int = preferences["max_search_results"]
        self._workspace_id = preferences["project"]

        self.tcli = tcli.TogglCli(self)

        self.notification = None

    def continue_tracker(self, *args) -> bool:
        img = CONTINUE_IMG
        cnt = self.tcli.continue_tracker(*args)
        noti = NotificationParameters(cnt, img)

        self.show_notification(noti)
        return True

    def start_tracker(self, *args) -> bool:
        # TODO: integrate @ for a project & # for tags
        img = START_IMG

        if len(args) == 1:
            return False
        return True

    def add_tracker(self, *args) -> bool:
        img = START_IMG

        msg = self.tcli.add_tracker(args[0])

        return True

    def edit_tracker(self, *args) -> None:
        img = EDIT_IMG

    def stop_tracker(self, *args) -> bool:
        img = STOP_IMG
        msg = self.tcli.stop_tracker()
        noti = NotificationParameters(str(msg), img)
        self.show_notification(noti)
        return True

    def remove_tracker(self, *args) -> None:
        img = DELETE_IMG

    def total_trackers(self, *args) -> None:
        img = REPORT_IMG

        return True

    def list_trackers(
        self, *args, post_method: Optional[MethodType] = None
    ) -> tuple[QueryParameters, ...]:
        img = REPORT_IMG
        trackers = self.tcli.list_trackers()
        return ()

    def show_notification(
        self, data: NotificationParameters, on_close: Optional[Callable] = None
    ) -> None:
        icon = str(data.icon.absolute())
        if not Notify.is_initted():
            Notify.init("TogglExtension")
        if self.notification is None:
            self.notification = Notify.Notification.new(data.title, data.body, icon)
        else:
            self.notification.update(data.title, data.body, icon)
        if on_close is not None:
            self.notification.connect("closed", on_close)
        self.notification.show()
