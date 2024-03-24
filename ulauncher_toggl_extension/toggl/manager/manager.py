from __future__ import annotations

import logging
import subprocess
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Callable, NamedTuple, Optional

from gi.repository import Notify
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction

from ulauncher_toggl_extension.toggl import (
    TogglTracker,
    TProject,
)
from ulauncher_toggl_extension.toggl.cli import (
    TogglProjects,
    TrackerCli,
)
from ulauncher_toggl_extension.toggl.images import (
    ADD_IMG,
    APP_IMG,
    CONTINUE_IMG,
    DELETE_IMG,
    EDIT_IMG,
    REPORT_IMG,
    START_IMG,
    STOP_IMG,
    TIP_IMAGES,
    TipSeverity,
)

if TYPE_CHECKING:
    from types import MethodType

    from ulauncher.api.shared.action.BaseAction import BaseAction

log = logging.getLogger(__name__)


class QueryParameters(NamedTuple):
    icon: Path
    name: str
    description: str
    on_enter: BaseAction
    on_alt_enter: Optional[BaseAction] = None
    small: bool = False


class TogglManager:
    """Manages interactions between extension and the cli and handles most of
    the logic between different states of the extension.

    Attributes:
        tcli: Toggl CLi instance which runs the TogglCli commands.
        pcli: Toggl Projects instance which runs any commands related to
            projects.
        notification: Notification instance used for displaying notifications
            and stored there when intialized.

    Methods:
       continue, add, start, stop, delete, report, edit: Executes through given
           cli command and returns a result.
       total_trackers: Displays a weekly total of tracker time.
       tracker | project builder: Creates description text and query parameters
           based on the given tracker.
       query_builder: Creates query parameters if the action is a
           SetUserQueryAction.
       notification_builder: Sends a notification to the system framework.
    """

    __slots__ = (
        "exec_path",
        "max_results",
        "default_project",
        "tcli",
        "pcli",
        "notification",
    )

    def __init__(
        self,
        config_path: Path,
        max_results: int,
        default_project: Optional[int] = None,
    ) -> None:
        self.exec_path = config_path
        self.max_results = max_results
        self.default_project = default_project

        self.tcli = TrackerCli(
            self.exec_path,
            self.max_results,
            self.default_project,
        )
        self.pcli = TogglProjects(
            self.exec_path,
            self.max_results,
            self.default_project,
        )

        self.notification = None

    def continue_tracker(self, *args, **kwargs) -> bool:
        try:
            msg = self.tcli.continue_tracker(*args, **kwargs)
        except subprocess.SubprocessError:
            return False

        self.show_notification(msg, CONTINUE_IMG)
        return True

    def start_tracker(self, *args, **kwargs) -> bool:
        if not args:
            return False
        if not isinstance(args[0], TogglTracker):
            tracker = TogglTracker(
                description=kwargs.get("description", ""),
                entry_id=0,
                stop=kwargs.get("stop", ""),
                start=kwargs.get("start", ""),
                project=kwargs.get("project", ""),
                duration=kwargs.get("duration"),
                tags=kwargs.get("tags"),
            )
        else:
            tracker = args[0]
            tracker.start = None

        try:
            msg = self.tcli.start_tracker(tracker)
            result = True
        except subprocess.SubprocessError:
            msg = f"Failed to start {tracker.description}"
            result = False

        self.show_notification(msg, START_IMG)

        return result

    def add_tracker(self, *args, **kwargs) -> bool:
        msg = self.tcli.add_tracker(*args, **kwargs)
        self.show_notification(msg, ADD_IMG)

        return True

    def edit_tracker(self, *_, **kwargs) -> bool:
        msg = self.tcli.edit_tracker(**kwargs)
        if msg == "Tracker is current not running." or msg is None:
            return False

        self.show_notification(msg, EDIT_IMG)

        return True

    def stop_tracker(self) -> bool:
        msg = self.tcli.stop_tracker()

        self.show_notification(msg, STOP_IMG)
        return True

    def remove_tracker(self, toggl_id: int | TogglTracker) -> bool:
        if isinstance(toggl_id, TogglTracker):
            toggl_id = int(toggl_id.entry_id)
        elif not isinstance(toggl_id, int):
            return False

        msg = self.tcli.rm_tracker(tracker=toggl_id)

        self.show_notification(msg, DELETE_IMG)
        return True

    def total_trackers(self) -> list[QueryParameters]:
        data = self.tcli.sum_tracker()
        queries = []
        for day, time in data:
            if day == "total":
                meth = DoNothingAction()
            else:
                if day == "today":
                    start = datetime.now(tz=UTC)
                elif day == "yesterday":
                    start = datetime.now(tz=UTC) - timedelta(days=1)
                else:
                    start = datetime.strptime(day, "%m/%d/%Y").astimezone(UTC)
                start -= timedelta(days=1)
                end = start + timedelta(days=2)

                meth = ExtensionCustomAction(
                    partial(
                        self.list_trackers,
                        start=start.date().isoformat(),
                        stop=end.date().isoformat(),
                    ),
                    keep_app_open=True,
                )
            param = QueryParameters(REPORT_IMG, day, time, meth)

            queries.append(param)

        return queries

    def list_trackers(self, *args, **kwargs) -> list[QueryParameters]:
        return self.create_list_actions(
            REPORT_IMG,
            refresh="refresh" in args,
            kwargs=kwargs,
        )

    def list_projects(
        self,
        *args,
        post_method=DoNothingAction,
        **kwargs,
    ) -> list[QueryParameters]:
        return self.create_list_actions(
            APP_IMG,
            text_formatter="Client: {client}",
            data_type="project",
            refresh="refresh" in args,
            post_method=post_method,
            **kwargs,
        )

    def tracker_builder(
        self,
        img: Path,
        meth: MethodType,
        text_formatter: str,
        tracker: TogglTracker,
    ) -> QueryParameters | None:
        text = tracker.stop
        if tracker.stop != "running":
            text = text_formatter.format(
                stop=tracker.stop,
                tid=tracker.entry_id,
                name=tracker.description,
                project=tracker.project[0],  # type: ignore[index]
                tags=tracker.tags,
                start=tracker.start,
                duration=tracker.duration,
            )
        else:
            return None

        return QueryParameters(
            tracker.find_color_svg(img),
            tracker.description,
            text,
            meth,
        )

    def project_builder(
        self,
        meth: MethodType,
        text_formatter: str,
        project: TProject,
    ) -> QueryParameters:
        text = text_formatter.format(
            name=project.name,
            project_id=project.project_id,
            client=project.client,
            color=project.color,
            active=project.active,
        )

        img = project.generate_color_svg()
        return QueryParameters(img, project.name, text, meth)

    def create_list_actions(  # noqa: PLR0913
        self,
        img: Path,
        post_method=DoNothingAction,
        custom_method: Optional[partial] = None,
        count_offset: int = 0,
        text_formatter: str = "Stopped: {stop}",
        *,
        keep_open: bool = False,
        refresh: bool = False,
        data_type: str = "tracker",
        **kwargs,
    ) -> list[QueryParameters]:
        if data_type == "tracker":
            list_data = self.tcli.fetch_objects(refresh=refresh, **kwargs)
        else:
            list_data = self.pcli.fetch_objects(refresh=refresh, **kwargs)

        queries = []
        for i, data in enumerate(list_data, start=1):
            if self.max_results - count_offset == i:
                break

            if post_method == self.query_builder:
                meth = post_method(data, kwargs["query"])
            elif custom_method is not None:
                func = partial(custom_method, data)
                meth = post_method(func, keep_app_open=keep_open)
            else:
                meth = post_method()

            if isinstance(data, TogglTracker):
                param = self.tracker_builder(
                    img,
                    meth,
                    text_formatter,
                    data,
                )
            else:
                param = self.project_builder(
                    meth,
                    text_formatter,
                    data,  # type: ignore[arg-type]
                )
            if param is None:
                continue

            queries.append(param)

        return queries

    def query_builder(
        self,
        info: TogglTracker | TProject,
        existing_query: list[str],
    ) -> SetUserQueryAction:
        joined_query = " ".join(existing_query)
        if isinstance(info, TogglTracker):
            if existing_query[1] == "start":
                extra_query = ""
                if info.description:
                    extra_query += f' "{info.description}"'
                if info.start:
                    extra_query += f" >{info.start}"
                if info.project:
                    pid: int = info.project[1]
                    extra_query += f" @{pid}"
                if info.tags and info.tags[0]:
                    tags = ",".join(info.tags) if len(info.tags) > 1 else info.tags[0]
                    extra_query += f" #{tags}"
            else:
                extra_query = str(info.entry_id)

        elif isinstance(info, TProject):
            extra_query = info.project_id
        else:
            return SetUserQueryAction(joined_query)

        new_query = f"{joined_query}{extra_query}"

        return SetUserQueryAction(new_query)

    def show_notification(
        self,
        msg: str,
        img: Path,
        title: str = "Toggl Extension",
        on_close: Optional[Callable] = None,
    ) -> None:
        icon = str(Path(__file__).parents[3] / img)
        if not Notify.is_initted():
            Notify.init("TogglExtension")
        if self.notification is None:
            self.notification = Notify.Notification.new(title, msg, icon)
        else:
            self.notification.update(title, msg, icon)
        if on_close is not None:
            self.notification.connect("closed", on_close)
        self.notification.show()

    def generate_hint(
        self,
        message: tuple[str, ...] | str,
        action: BaseAction = DoNothingAction(),  # noqa: B008
        level: TipSeverity = TipSeverity.INFO,
        *,
        small: bool = True,
    ) -> list[QueryParameters]:
        img = TIP_IMAGES.get(level)

        if not isinstance(img, Path):
            msg = "Level | Severity was not found."
            raise TypeError(msg)

        title = level.name.title()
        if isinstance(message, str):
            param = QueryParameters(img, title, message, action, small=small)
            return [param]

        hints = []

        for desc in message:
            param = QueryParameters(img, title, desc, action, small=small)
            hints.append(param)

        return hints
