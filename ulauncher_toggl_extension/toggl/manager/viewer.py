from __future__ import annotations

from functools import cache, partial
from typing import TYPE_CHECKING

from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction

from ulauncher_toggl_extension.toggl import TogglTracker
from ulauncher_toggl_extension.toggl.cli import TrackerCli
from ulauncher_toggl_extension.toggl.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    CONTINUE_IMG,
    DELETE_IMG,
    EDIT_IMG,
    REPORT_IMG,
    START_IMG,
    STOP_IMG,
)

from .manager import QueryParameters, TipSeverity, TogglManager

if TYPE_CHECKING:
    from ulauncher.api.shared.action.BaseAction import BaseAction

    from ulauncher_toggl_extension.extension import TogglExtension


class TogglViewer:
    """Class that creates a bridge between the extension, TogglCli & Manager.

    Mostly deals with displaying information in the ULauncher UI.

    Args:
        ext(TogglExtension): Extension instance which provides user
            preferences.

    Methods:
        pre_check_cli: Checks if TogglCli exists at provided path and returns
            error message if it doesn't. Might refactor to user perferences.
        default_options: Returns default options for the base extension query.
        continue, add, start, stop, delete, report, edit: Displays or executes
            relevant actions.
        check_current_tracker: Checks if there is a running Toggl tracker and
            displays information relevant to it.
        generate_basic_hints: Generates hints for the base extension query.
        list_trackers | list_projects: Lists the latest trackers or projects
            in the cli.
    """

    __slots__ = (
        "max_results",
        "default_project",
        "tcli",
        "manager",
        "extension",
        "hints",
        "current_tracker",
        "toggl_exec_path",
    )

    def __init__(self, extension: TogglExtension) -> None:
        self.toggl_exec_path = extension.toggl_exec_path
        self.max_results = extension.max_results
        self.default_project = extension.default_project
        self.hints = extension.toggled_hints

        self.tcli = TrackerCli(
            extension.toggl_exec_path,
            extension.max_results,
            extension.default_project,
        )
        self.manager = TogglManager(
            extension.toggl_exec_path,
            extension.max_results,
            extension.default_project,
        )

        self.current_tracker = self.tcli.check_running()

    def pre_check_cli(self) -> list | None:
        # TODO: Refactor pre check into preferences at some other point.
        if not self.toggl_exec_path.exists():
            ext_warning = self.manager.generate_hint(
                "TogglCli is not properly configured.",
                SetUserQueryAction(""),
                TipSeverity.ERROR,
                small=False,
            )
            ext_warning.extend(
                self.manager.generate_hint(
                    "Check your Toggl exectutable path in the config.",
                    DoNothingAction(),
                    TipSeverity.INFO,
                ),
            )
            return ext_warning

        return None

    def default_options(self, *args, **kwargs) -> list[QueryParameters]:
        basic_tasks = [
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
            self.list_projects(*args, **kwargs)[0],
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
                ),
            ]
        else:
            proj = self.current_tracker.project
            proj = proj[0] if proj else ""
            desc = f"Since: {self.current_tracker.start}"
            if proj:
                desc += f" @{proj}"
            # TODO: Refactor into a custom method/function for reusability.
            current = [
                QueryParameters(
                    self.current_tracker.find_color_svg(APP_IMG),
                    f"Currently Running: {self.current_tracker.description}",
                    desc,
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

        current.extend(basic_tasks)

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
            ),
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
            ),
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
        msg = "Add a new tracker{0}."
        desc = kwargs.get("description", "")
        msg = msg.format(f" with description {desc}" if desc else "")

        base_param = [
            QueryParameters(
                ADD_IMG,
                "Add",
                msg,
                ExtensionCustomAction(
                    partial(self.manager.add_tracker, *args, **kwargs),
                    keep_app_open=True,
                ),
                SetUserQueryAction("tgl add"),
            ),
        ]

        base_param.extend(self.generate_basic_hints())

        return base_param

    def check_current_tracker(self) -> TogglTracker | list[QueryParameters]:
        if not isinstance(self.current_tracker, TogglTracker):
            return self.manager.generate_hint(
                "No active tracker is running.",
                SetUserQueryAction("tgl "),
                TipSeverity.ERROR,
                small=False,
            )

        return self.current_tracker

    def edit_tracker(
        self,
        *args,
        **kwargs,
    ) -> list[QueryParameters] | TogglTracker:
        track = self.check_current_tracker()
        if not isinstance(track, TogglTracker):
            return track

        params = [
            QueryParameters(
                track.find_color_svg(EDIT_IMG),
                track.description,
                "Edit the running tracker.",
                ExtensionCustomAction(
                    partial(self.manager.edit_tracker, *args, **kwargs),
                    keep_app_open=True,
                ),
                SetUserQueryAction("tgl edit"),
            ),
        ]
        data = self.create_tracker_subinfo(track)
        params.extend(self.manager.generate_hint(data))
        params.extend(self.generate_basic_hints())

        return params

    def create_tracker_subinfo(self, track: TogglTracker) -> tuple:
        data = [f"Started {track.start}"]
        if isinstance(track.project, str):
            data.append(f"{track.project}")

        if track.tags:
            if len(track.tags) == 1 or isinstance(track.tags, str):
                data.append(f"{track.tags}")
            else:
                data.append(", ".join(track.tags))

        return tuple(data)

    def stop_tracker(self, *_, **__) -> list[QueryParameters]:
        track = self.check_current_tracker()
        if not isinstance(track, TogglTracker):
            return track

        params = [
            QueryParameters(
                STOP_IMG,
                "Stop",
                f"Stop tracking {track.description}.",
                ExtensionCustomAction(
                    partial(self.manager.stop_tracker),
                    keep_app_open=False,
                ),
                SetUserQueryAction("tgl stop"),
            ),
        ]

        data = self.create_tracker_subinfo(track)
        project = self.manager.generate_hint(data)
        params.extend(project)

        return params

    def remove_tracker(self, *args, **kwargs) -> list[QueryParameters]:
        params = [
            QueryParameters(
                DELETE_IMG,
                "Delete",
                "Delete tracker.",
                ExtensionCustomAction(
                    partial(self.manager.remove_tracker, *args, **kwargs),
                    keep_app_open=False,
                ),
                SetUserQueryAction("tgl delete"),
            ),
        ]
        trackers = self.manager.create_list_actions(
            img=DELETE_IMG,
            post_method=ExtensionCustomAction,
            custom_method=partial(self.manager.remove_tracker),
            count_offset=-1,
            text_formatter="Delete tracker {name}",
        )

        params.extend(trackers)

        return params

    def total_trackers(self, *_, **__) -> list[QueryParameters]:
        params = QueryParameters(
            REPORT_IMG,
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
        params = QueryParameters(
            BROWSER_IMG,
            "List",
            f"View the last {self.max_results} trackers.",
            ExtensionCustomAction(
                partial(self.manager.list_trackers, *args, **kwargs),
                keep_app_open=True,
            ),
            SetUserQueryAction("tgl list"),
        )
        return [params]

    def list_projects(self, *args, **kwargs) -> list[QueryParameters]:
        # TODO: Implement more project actions
        data = QueryParameters(
            APP_IMG,
            "Projects",
            "View all your projects.",
            ExtensionCustomAction(
                partial(self.manager.list_projects, *args, **kwargs),
                keep_app_open=True,
            ),
            SetUserQueryAction("tgl project"),
        )
        return [data]

    @cache  # noqa: B019
    def generate_basic_hints(
        self,
        *,
        max_values: int = 5,
        default_action: BaseAction = DoNothingAction,
        **_,
    ) -> list[QueryParameters]:
        # TODO: Explore more clear html formatting.
        if not self.hints:
            return []

        default_action = default_action()

        hint_messages = (
            "Set the description with surrounding quotes.",
            "Set a project with the @ symbol",
            "Add tags with the # symbol.",
            "Set the start time with '<'",
            "Set the end time with '>'",
            "Set the duation with '>' and '<'",
            "Time formatting expects default TogglCli formatting.",
        )
        return self.manager.generate_hint(
            hint_messages[:max_values],
            action=default_action,
        )
