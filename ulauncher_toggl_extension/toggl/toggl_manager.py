import logging as log
from functools import cache, partial
from pathlib import Path
from types import MethodType
from typing import TYPE_CHECKING, Callable, NamedTuple, Optional

from gi.repository import Notify
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

# TODO: Integrate this instead of cli + as soon 3.12v exists for the API
## from toggl import api, tuils
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction

from ulauncher_toggl_extension.toggl import toggl_cli as tcli

if TYPE_CHECKING:
    from main import TogglExtension

APP_IMG = Path("images/icon.svg")
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
    __slots__ = (
        "_config_path",
        "_max_results",
        "_workspace_id",
        "cli",
        "manager",
        "extension",
    )

    def __init__(self, ext: "TogglExtension") -> None:
        self._config_path = ext.config_path
        self._max_results = ext.max_results
        self._workspace_id = ext.workspace_id

        self.cli = tcli.TogglCli(ext.config_path, ext.max_results, ext.workspace_id)
        self.manager = TogglManager(ext)

    def default_options(self, *args) -> list[QueryParameters]:
        BASIC_TASKS = [
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
                ExtensionCustomAction(
                    partial(self.manager.stop_tracker, *args),
                    keep_app_open=False,
                ),
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
                    partial(self.manager.list_trackers), keep_app_open=True
                ),
            ),
        ]

        current = self.cli.check_running()
        if current is None:
            current = QueryParameters(
                CONTINUE_IMG,
                "Continue",
                "Continue the latest Toggl time tracker",
                SetUserQueryAction("tgl cnt"),
            )
        else:
            current = QueryParameters(
                APP_IMG,
                f"Currently Running: {current.description}",
                f"Since: {current.start} @{current.project}",
                DoNothingAction(),
            )

        BASIC_TASKS.insert(0, current)

        return BASIC_TASKS

    def continue_tracker(self, *args) -> list[QueryParameters]:
        img = CONTINUE_IMG

        base_param = [
            QueryParameters(
                img,
                "Continue",
                "Continue the last tracker.",
                ExtensionCustomAction(
                    partial(self.manager.continue_tracker, *args),
                    keep_app_open=False,
                ),
            )
        ]

        return base_param

    def start_tracker(self, *args) -> list[QueryParameters]:
        # TODO: integrate @ for a project & # for tags
        img = START_IMG

        base_param = [
            QueryParameters(
                img,
                "Start",
                "Start a new tracker.",
                ExtensionCustomAction(
                    partial(self.manager.start_tracker, *args),
                    keep_app_open=False,
                ),
            )
        ]

        trackers = self.manager.create_list_actions(
            img=img,
            post_method=ExtensionCustomAction,
            custom_method=partial(self.manager.start_tracker),
            count_offset=-1,
            text_formatter="Start tracking {name}",
        )

        base_param.extend(trackers)

        return base_param

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
        "config_path",
        "max_results",
        "workspace_id",
        "cli",
        "notification",
    )

    def __init__(self, ext: "TogglExtension") -> None:
        self.config_path = ext.config_path
        self.max_results = ext.max_results
        self.workspace_id = ext.workspace_id

        self.cli = tcli.TogglCli(ext.config_path, ext.max_results, ext.workspace_id)

        self.notification = None

    def continue_tracker(self, *args) -> bool:
        img = CONTINUE_IMG

        cnt = self.cli.continue_tracker(*args)
        noti = NotificationParameters(cnt, img)

        self.show_notification(noti)
        return True

    def start_tracker(self, *args) -> bool:
        # TODO: integrate @ for a project & # for tags
        img = START_IMG

        if args and isinstance(args[0], tcli.TogglTracker):
            name = f'"{args[0].description}"'
        else:
            return False

        cnt = self.cli.start_tracker(name=name)
        noti = NotificationParameters(cnt, img)

        self.show_notification(noti)
        return True

    def add_tracker(self, *args) -> bool:
        img = START_IMG
        msg = self.cli.add_tracker(args[0])

        return True

    def edit_tracker(self, *args) -> None:
        img = EDIT_IMG

    def stop_tracker(self, *args) -> bool:
        img = STOP_IMG
        msg = self.cli.stop_tracker()
        noti = NotificationParameters(str(msg), img)
        self.show_notification(noti)
        return True

    def remove_tracker(self, *args) -> bool:
        img = DELETE_IMG
        return True

    def total_trackers(self, *args) -> list[QueryParameters]:
        img = REPORT_IMG

        data = self.cli.sum_tracker()
        queries = []
        for day, time in data:
            param = QueryParameters(img, day, time, DoNothingAction())
            # TODO: Possibly could show a break down of the topx trackers in
            # the future.
            queries.append(param)

        return queries

    def list_trackers(
        self,
        *args,
    ) -> list[QueryParameters]:
        img = REPORT_IMG

        return self.create_list_actions(img)

    def create_list_actions(
        self,
        img: Path,
        post_method=DoNothingAction,
        custom_method: Optional[partial] = None,
        count_offset: int = 0,
        text_formatter: str = "Stopped: {stop}",
        keep_open: bool = False,
    ) -> list[QueryParameters]:
        trackers = self.cli.list_trackers(refresh=True)
        queries = []

        for i, tracker in enumerate(trackers, start=1):
            if self.max_results - count_offset == i:
                break

            if custom_method is not None:
                func = partial(custom_method, tracker)
                meth = post_method(func, keep_app_open=keep_open)
            else:
                meth = post_method()

            text = tracker.stop
            if tracker.stop != "running":
                text = text_formatter.format(
                    stop=tracker.stop,
                    tid=tracker.entry_id,
                    name=tracker.description,
                    project=tracker.project,
                    tags=tracker.tags,
                    start=tracker.start,
                    duration=tracker.duration,
                )

            param = QueryParameters(
                img,
                tracker.description,
                text,
                meth,
            )
            queries.append(param)

        return queries

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
