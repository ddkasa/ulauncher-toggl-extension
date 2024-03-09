import enum
import logging
import subprocess as sp
from datetime import datetime, timedelta
from functools import cache, partial
from pathlib import Path
from types import MethodType
from typing import TYPE_CHECKING, Callable, NamedTuple, Optional

import gi
from gi.repository import Notify
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction

from ulauncher_toggl_extension.toggl.toggl_cli import (
    TogglProjects,
    TogglTracker,
    TProject,
    TrackerCli,
)

gi.require_version("Notify", "0.7")
# TODO: Integrate this instead of cli + as soon 3.12v exists for the API
## from toggl import api, tuils

# from ulauncher_toggl_extension import utils
# utils.ensure_import("togglcli")

if TYPE_CHECKING:
    from main import TogglExtension

log = logging.getLogger(__name__)

SVG_PATH = Path("images/svg")

APP_IMG = SVG_PATH / Path("icon.svg")
START_IMG = SVG_PATH / Path("start.svg")
EDIT_IMG = SVG_PATH / Path("edit.svg")
ADD_IMG = SVG_PATH / Path("add.svg")
# PROJECT_IMG = SVG_PATH / Path("project.svg")  # TODO: Needs to be created.
STOP_IMG = SVG_PATH / Path("stop.svg")
DELETE_IMG = SVG_PATH / Path("delete.svg")
CONTINUE_IMG = SVG_PATH / Path("continue.svg")
REPORT_IMG = SVG_PATH / Path("reports.svg")
BROWSER_IMG = SVG_PATH / Path("browser.svg")
BLANK_IMG = SVG_PATH / Path("blank.svg")


class TipSeverity(enum.Enum):
    INFO = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()


TIP_IMAGES = {
    TipSeverity.INFO: SVG_PATH / Path("tip.svg"),
    TipSeverity.ERROR: SVG_PATH / Path("tip-error.svg"),
    TipSeverity.WARNING: SVG_PATH / Path("tip-warning.svg"),
}


class QueryParameters(NamedTuple):
    icon: Path
    name: str
    description: str
    on_enter: BaseAction
    on_alt_enter: Optional[BaseAction] = None
    small: bool = False


class TogglViewer:
    __slots__ = (
        "toggl_exec_path",
        "max_results",
        "default_project",
        "tcli",
        "manager",
        "extension",
        "hints",
        "current_tracker",
    )

    def __init__(self, ext: "TogglExtension") -> None:
        self.toggl_exec_path = ext.toggl_exec_path
        self.max_results = ext.max_results
        self.default_project = ext.default_project
        self.hints = ext.toggled_hints

        self.tcli = TrackerCli(
            self.toggl_exec_path, self.max_results, self.default_project
        )
        self.manager = TogglManager(
            self.toggl_exec_path, self.max_results, self.default_project
        )

        self.current_tracker = self.tcli.check_running()

    def pre_check_cli(self) -> list | None:
        if not self.toggl_exec_path.exists():
            warning = self.manager.generate_hint(
                "TogglCli is not properly configured.",
                SetUserQueryAction(""),
                TipSeverity.ERROR,
                small=False,
            )
            warning.extend(
                self.manager.generate_hint(
                    "Check your Toggl exectutable path in the config.",
                    DoNothingAction(),
                    TipSeverity.INFO,
                ),
            )
            return warning

        return None

    def default_options(self, *args, **kwargs) -> list[QueryParameters]:
        BASIC_TASKS = [
            QueryParameters(
                START_IMG,
                "Start",
                "Start a Toggl tracker",
                SetUserQueryAction("tgl start"),
            ),
            QueryParameters(
                START_IMG,
                "Add",
                "Add a toggl time tracker.",
                SetUserQueryAction("tgl add"),
            ),
            QueryParameters(
                DELETE_IMG,
                "Delete",
                "Delete a Toggl time tracker",
                SetUserQueryAction("tgl delete"),
            ),
            self.total_trackers()[0],
            self.list_trackers(*args, **kwargs)[0],
            self.get_projects(*args, **kwargs)[0],
        ]
        if self.current_tracker is None:
            current = [
                QueryParameters(
                    CONTINUE_IMG,
                    "Continue",
                    "Continue the latest Toggl time tracker",
                    ExtensionCustomAction(
                        partial(self.manager.continue_tracker),
                    ),
                    SetUserQueryAction("tgl continue"),
                )
            ]
        else:
            current = [
                QueryParameters(
                    APP_IMG,
                    f"Currently Running: {self.current_tracker.description}",
                    f"Since: {self.current_tracker.start} @{self.current_tracker.project}",
                    ExtensionCustomAction(
                        partial(
                            self.edit_tracker,
                            current=self.current_tracker,
                        ),
                        keep_app_open=True,
                    ),
                ),
                self.stop_tracker()[0],
            ]

        current.extend(BASIC_TASKS)

        return current

    def continue_tracker(self, *args, **kwargs) -> list[QueryParameters]:
        img = CONTINUE_IMG

        base_param = [
            QueryParameters(
                img,
                "Continue",
                "Continue the last tracker.",
                ExtensionCustomAction(
                    partial(self.manager.continue_tracker, *args, **kwargs),
                    keep_app_open=False,
                ),
                SetUserQueryAction("tgl continue"),
            )
        ]
        trackers = self.manager.create_list_actions(
            img=img,
            post_method=ExtensionCustomAction,
            custom_method=partial(
                self.manager.continue_tracker,
                *args,
                **kwargs,
            ),
            count_offset=-1,
            text_formatter="Continue {name} @{project}",
        )
        base_param.extend(trackers)

        return base_param

    def start_tracker(self, *args, **kwargs) -> list[QueryParameters]:
        img = START_IMG
        base_param = [
            QueryParameters(
                img,
                "Start",
                "Start a new tracker.",
                ExtensionCustomAction(
                    partial(self.manager.start_tracker, *args, **kwargs),
                    keep_app_open=False,
                ),
                SetUserQueryAction("tgl start"),
            )
        ]
        fresh_query = ["tgl", "start"]
        fresh_query.extend(args)
        trackers = self.manager.create_list_actions(
            img=img,
            post_method=self.manager.query_builder,
            count_offset=-1,
            text_formatter="Start {name} @{project}",
            query=fresh_query,
        )

        base_param.extend(trackers)

        return base_param

    def add_tracker(self, *args, **kwargs) -> list[QueryParameters]:
        img = ADD_IMG
        msg = "Add a new tracker"
        if args:
            msg += f" with description {args[0]}."
        else:
            msg += "."

        base_param = [
            QueryParameters(
                img,
                "Add",
                msg,
                ExtensionCustomAction(
                    partial(self.manager.add_tracker, *args, **kwargs),
                    keep_app_open=True,
                ),
                SetUserQueryAction("tgl add"),
            )
        ]

        base_param.extend(self.generate_basic_hints())

        return base_param

    def check_current_tracker(self):
        if not isinstance(self.current_tracker, TogglTracker):
            reset = self.manager.generate_hint(
                "No active tracker is running.",
                SetUserQueryAction("tgl "),
                TipSeverity.ERROR,
                small=False,
            )
            return reset

        return self.current_tracker

    def edit_tracker(self, *args, **kwargs) -> list[QueryParameters]:
        img = EDIT_IMG

        track = self.check_current_tracker()
        if not isinstance(track, TogglTracker):
            return track

        params = [
            QueryParameters(
                img,
                track.description,
                "Edit the running tracker.",
                ExtensionCustomAction(
                    partial(self.manager.edit_tracker, *args, **kwargs),
                    keep_app_open=True,
                ),
                SetUserQueryAction("tgl edit"),
            )
        ]
        data = self.create_tracker_subinfo(track)
        params.extend(self.manager.generate_hint(data))
        params.extend(self.generate_basic_hints())

        return params

    def create_tracker_subinfo(self, track: TogglTracker) -> tuple:
        data = [f"Started {track.start}"]
        if isinstance(track.project, str):
            data.append(f"{track.project}")

        if track.tags and isinstance(track.tags, (str, list)):
            if isinstance(track.tags, str):
                data.append(f"{track.tags}")
            else:
                data.append(", ".join(track.tags))
        return tuple(data)

    def stop_tracker(self, *args, **kwargs) -> list[QueryParameters]:
        del args, kwargs
        img = STOP_IMG
        track = self.check_current_tracker()
        if not isinstance(track, TogglTracker):
            return track
        params = [
            QueryParameters(
                img,
                "Stop",
                f"Stop tracking {track.description}.",
                ExtensionCustomAction(
                    partial(self.manager.stop_tracker),
                    keep_app_open=False,
                ),
                SetUserQueryAction("tgl stop"),
            )
        ]

        data = self.create_tracker_subinfo(track)
        project = self.manager.generate_hint(data)
        params.extend(project)

        return params

    def remove_tracker(self, *args, **kwargs) -> list[QueryParameters]:
        img = DELETE_IMG
        params = [
            QueryParameters(
                img,
                "Delete",
                "Delete tracker.",
                ExtensionCustomAction(
                    partial(self.manager.remove_tracker, *args, **kwargs),
                    keep_app_open=False,
                ),
                SetUserQueryAction("tgl delete"),
            )
        ]
        trackers = self.manager.create_list_actions(
            img=img,
            post_method=ExtensionCustomAction,
            custom_method=partial(self.manager.remove_tracker),
            count_offset=-1,
            text_formatter="Delete tracker {name}",
        )

        params.extend(trackers)

        return params

    def total_trackers(self) -> list[QueryParameters]:
        img = REPORT_IMG

        params = QueryParameters(
            img,
            "Generate Report",
            "View a weekly total of your trackers.",
            ExtensionCustomAction(
                partial(self.manager.total_trackers),
                keep_app_open=True,
            ),
            SetUserQueryAction("tgl report"),
        )
        return [params]

    def list_trackers(self, *args, **kwargs) -> list[QueryParameters]:
        img = BROWSER_IMG
        params = QueryParameters(
            img,
            "List",
            f"View the last {self.max_results} trackers.",
            ExtensionCustomAction(
                partial(self.manager.list_trackers, *args, **kwargs),
                keep_app_open=True,
            ),
            SetUserQueryAction("tgl list"),
        )
        return [params]

    def get_projects(self, *args, **kwargs) -> list[QueryParameters]:
        img = APP_IMG
        data = QueryParameters(
            img,
            "Projects",
            "View & Edit projects.",
            ExtensionCustomAction(
                partial(self.manager.list_projects, *args, **kwargs),
                keep_app_open=True,
            ),
            SetUserQueryAction("tgl project"),
        )
        return [data]

    @cache
    def generate_basic_hints(
        self,
        max_values: int = 3,
        default_action: BaseAction = DoNothingAction(),
    ) -> list[QueryParameters]:
        # TODO: Explore more clear html formatting.
        if not self.hints:
            return []

        HINT_MESSAGES = (
            "Set a project with the @ symbol",
            "Add tags with the # symbol.",
            "Set the start and end time with > & < respectively and the duration with both.",
            "If using spaces in your trackers or projects use quotation marks.",
            "Time formatting expects default TogglCli formatting.",
        )
        hints = self.manager.generate_hint(
            HINT_MESSAGES[:max_values], action=default_action
        )
        return hints


class TogglManager:
    __slots__ = (
        "exec_path",
        "max_results",
        "workspace_id",
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
        self.workspace_id = default_project

        self.tcli = TrackerCli(
            self.exec_path,
            self.max_results,
            self.workspace_id,
        )
        self.pcli = TogglProjects(
            self.exec_path,
            self.max_results,
            self.workspace_id,
        )

        self.notification = None

    def continue_tracker(self, *args, **kwargs) -> bool:
        img = CONTINUE_IMG

        msg = self.tcli.continue_tracker(*args, **kwargs)

        self.show_notification(msg, img)
        return True

    def start_tracker(self, *args, **kwargs) -> bool:
        # TODO: To similar to continue in certain functionality, so it needs some adjustments.
        img = START_IMG

        if not args:
            return False
        elif not isinstance(args[0], TogglTracker):
            tracker = TogglTracker(
                description=str(args[0]),
                entry_id=0,
                stop=kwargs.get("stop", ""),
                project=kwargs.get("project"),
                duration=kwargs.get("duration"),
                tags=kwargs.get("tags"),
            )
        else:
            tracker = args[0]
            tracker.start = None

        try:
            msg = self.tcli.start_tracker(tracker)
            result = True
        except sp.SubprocessError:
            msg = f"Failed to start {tracker.description}"
            result = False

        self.show_notification(msg, img)

        return result

    def add_tracker(self, *args, **kwargs) -> bool:
        img = ADD_IMG

        msg = self.tcli.add_tracker(*args, **kwargs)
        self.show_notification(msg, img)

        return True

    def edit_tracker(self, *args, **kwargs) -> bool:
        img = EDIT_IMG

        msg = self.tcli.edit_tracker(*args, **kwargs)
        if msg == "Tracker is current not running." or msg is None:
            return False

        self.show_notification(msg, img)

        return True

    def stop_tracker(self) -> bool:
        img = STOP_IMG
        msg = self.tcli.stop_tracker()

        self.show_notification(msg, img)
        return True

    def remove_tracker(self, toggl_id: int | TogglTracker) -> bool:
        if isinstance(toggl_id, TogglTracker):
            toggl_id = int(toggl_id.entry_id)
        elif not isinstance(toggl_id, int):
            return False

        img = DELETE_IMG

        msg = self.tcli.rm_tracker(tracker=toggl_id)

        self.show_notification(msg, img)
        return True

    def total_trackers(self) -> list[QueryParameters]:
        img = REPORT_IMG

        data = self.tcli.sum_tracker()
        queries = []
        for day, time in data:
            if day == "total":
                meth = DoNothingAction()
            else:
                if day == "today":
                    start = datetime.now()
                elif day == "yesterday":
                    start = datetime.now() - timedelta(days=1)
                else:
                    start = datetime.strptime(day, "%m/%d/%Y")
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
            param = QueryParameters(img, day, time, meth)

            queries.append(param)

        return queries

    def list_trackers(self, *args, **kwargs) -> list[QueryParameters]:
        img = REPORT_IMG

        return self.create_list_actions(
            img,
            refresh="refresh" in args,
            kwargs=kwargs,
        )

    def list_projects(
        self, *args, post_method=DoNothingAction, **kwargs
    ) -> list[QueryParameters]:
        img = APP_IMG
        data = self.create_list_actions(
            img,
            text_formatter="Client: {client}",
            data_type="project",
            refresh="refresh" in args,
            post_method=post_method,
            **kwargs,
        )
        return data

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
                project=tracker.project,
                tags=tracker.tags,
                start=tracker.start,
                duration=tracker.duration,
            )
        else:
            return None

        param = QueryParameters(
            img,
            tracker.description,
            text,
            meth,
        )
        return param

    def project_builder(
        self,
        img: Path,
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
        param = QueryParameters(img, project.name, text, meth)
        return param

    def create_list_actions(
        self,
        img: Path,
        post_method=DoNothingAction,
        custom_method: Optional[partial] = None,
        count_offset: int = 0,
        text_formatter: str = "Stopped: {stop}",
        keep_open: bool = False,
        refresh: bool = False,
        data_type: str = "tracker",
        **kwargs,
    ) -> list[QueryParameters]:
        if data_type == "tracker":
            list_data = self.tcli.list_trackers(refresh=refresh, **kwargs)
        else:
            list_data = self.pcli.list_projects(refresh=refresh, **kwargs)

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
                param = self.tracker_builder(img, meth, text_formatter, data)
            else:
                param = self.project_builder(img, meth, text_formatter, data)

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
                    _, pid = TogglProjects.project_name_formatter(
                        info.project  # type: ignore
                    )
                    extra_query += f" @{pid}"
                if info.tags:
                    print(info.tags)
                    extra_query += f" #{','.join(info.tags)}"
            else:
                extra_query = str(info.entry_id)

        elif isinstance(info, TProject):
            extra_query = info.project_id  # type: ignore
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
        icon = str(Path(__file__).parents[2] / img)
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
        action: BaseAction = DoNothingAction(),
        level: TipSeverity = TipSeverity.INFO,
        small: bool = True,
    ) -> list[QueryParameters]:
        img = TIP_IMAGES.get(level)

        if not isinstance(img, Path):
            raise AttributeError("Level | Severity was not found.")

        title = level.name.title()
        if isinstance(message, str):
            param = QueryParameters(img, title, message, action, small=small)
            return [param]

        hints = []

        for desc in message:
            param = QueryParameters(img, title, desc, action, small=small)
            hints.append(param)

        return hints
