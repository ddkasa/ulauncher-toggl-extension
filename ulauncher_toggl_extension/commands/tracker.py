from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import TYPE_CHECKING, Any, Optional

from httpx import HTTPStatusError
from toggl_api import (
    TogglProject,
    TogglTracker,
    TrackerBody,
    TrackerEndpoint,
    UserEndpoint,
)

from ulauncher_toggl_extension.date_time import display_dt, get_local_tz
from ulauncher_toggl_extension.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    CONTINUE_IMG,
    DELETE_IMG,
    EDIT_IMG,
    START_IMG,
    STOP_IMG,
    TIP_IMAGES,
    TipSeverity,
)

from .meta import ACTION_TYPE, ActionEnum, Command, QueryParameters
from .project import ProjectCommand
from .tag import TagCommand

if TYPE_CHECKING:
    from pathlib import Path


log = logging.getLogger(__name__)


class TrackerCommand(Command):
    """Base Tracker command setting up default methods."""

    def process_model(  # noqa: PLR0913
        self,
        model: TogglTracker,
        action: ACTION_TYPE,
        alt_action: Optional[ACTION_TYPE] = None,
        *,
        advanced: bool = False,
        fmt_str: str = "{prefix} {name}",
    ) -> list[QueryParameters]:
        name = fmt_str.format(prefix=self.PREFIX.title(), name=model.name)
        cmd = ProjectCommand(self)
        project = cmd.get_project(model.project)
        path = self.get_icon(project)
        description = f"@{project.name if project else model.project}" or ""
        if model.tags:
            description += f" #{','.join(tag.name for tag in model.tags)}"

        queries = [
            QueryParameters(
                path,
                name,
                description,
                action,
                alt_action,
            ),
        ]
        if advanced:
            dates = self.format_datetime(model)
            total_time = (
                model.duration
                if model.stop
                else datetime.now(timezone.utc) - model.start
            )

            extra = [
                QueryParameters(
                    START_IMG,
                    dates[0],
                    "",
                    on_enter=ActionEnum.DO_NOTHING,
                    small=True,
                ),
                QueryParameters(
                    APP_IMG,
                    f"Duration: {round(total_time.total_seconds() / 3600, 2)}h",
                    on_enter=ActionEnum.DO_NOTHING,
                    small=True,
                ),
            ]

            if dates[1]:
                extra.insert(
                    1,
                    QueryParameters(
                        STOP_IMG,
                        dates[1],
                        "",
                        on_enter=ActionEnum.DO_NOTHING,
                        small=True,
                    ),
                )

            queries.extend(extra)

        return queries

    @staticmethod
    def format_datetime(model: TogglTracker) -> tuple[str, str]:
        if not model.stop:
            text = f"Running since {display_dt(model.start)}!"
            return text, ""
        return (
            f"Started at {display_dt(model.start)}",
            f"Stopped at {display_dt(model.stop)}",
        )

    def get_icon(self, project: Optional[TogglProject] = None) -> Path:
        if project is None or not project.color:
            return self.ICON

        path = self.cache_path / f"svg/{project.color}.svg"

        if not path.exists():
            cmd = ProjectCommand(self)
            cmd.generate_color_svg(project)

        return path

    def get_models(self, **kwargs) -> list[TogglTracker]:
        """Collects trackers and filters and sorts them for further use."""
        user = UserEndpoint(self.workspace_id, self.auth, self.cache)
        trackers = user.get_trackers(
            kwargs.get("start"),
            kwargs.get("stop"),
            kwargs.get("end_data"),
            kwargs.get("start_date"),
            refresh=kwargs.get("refresh", False),
        )
        trackers.sort(
            key=lambda x: (x.stop or datetime.now(tz=timezone.utc), x.start),
            reverse=True,
        )
        if kwargs.get("distinct", True):
            data: list[TogglTracker] = []
            for tracker in trackers:
                if self.distinct(tracker, data):
                    data.append(tracker)

            return data

        return trackers

    @staticmethod
    def distinct(tracker: TogglTracker, data: list[TogglTracker]) -> bool:
        for t in data:
            if (
                tracker.name == t.name
                and tracker.tags == t.tags
                and tracker.project == t.project
            ):
                return False

        return True

    def get_current_tracker(
        self,
        *,
        refresh: bool = True,
    ) -> Optional[TogglTracker]:
        user = UserEndpoint(self.workspace_id, self.auth, self.cache)
        return user.current_tracker(refresh=refresh)

    def autocomplete(self, query: list[str], **kwargs) -> list[QueryParameters]:
        query = query.copy()
        query.insert(0, self.prefix)
        autocomplete: list[QueryParameters] = []
        if not self.check_autocmp(query):
            return autocomplete

        if query[-1][0] == '"' and query[-1][-1] != '"':
            cmd = ProjectCommand(self)
            models = self.get_models(**kwargs)

            for model in models:
                query[-1] = f'"{model.name}"'
                project = cmd.get_project(model.project)
                autocomplete.append(
                    QueryParameters(
                        self.get_icon(project),
                        model.name,
                        "Use this tracker description.",
                        " ".join(query),
                    ),
                )

        elif query[-1][0] == "@" and len(query[-1]) < 4:  # noqa: PLR2004
            cmd = ProjectCommand(self)

            for model in cmd.get_models(**kwargs):
                query[-1] = f"@{model.id}"
                autocomplete.append(
                    QueryParameters(
                        cmd.get_icon(model),
                        model.name,
                        "Use this project.",
                        " ".join(query),
                    ),
                )

        elif query[-1][0] == "#" and (len(query[-1]) < 3 or query[-1][-1] == ","):  # noqa: PLR2004
            cmd = TagCommand(self)

            for model in cmd.get_models(**kwargs):
                if "," in query[-1]:
                    query[-1] = query[-1][: query[-1].rfind(",")] + f",{model.name}"
                else:
                    query[-1] = f"#{model.name}"
                autocomplete.append(
                    QueryParameters(
                        cmd.ICON,
                        model.name,
                        "Use this tag.",
                        " ".join(query),
                    ),
                )

        elif query[-1][0] in {">", "<"}:
            # TODO: Autocomplete possibility for dates and time.
            pass

        return autocomplete

    @classmethod
    def sanitize_start_time(cls, **kwargs) -> dict[str, Any]:
        start = kwargs.get("start")
        if start:
            now = datetime.now(tz=timezone.utc)
            if start > now:
                kwargs["start"] = now

            stop = kwargs.get("stop")
            if stop:
                if stop <= kwargs["start"]:
                    kwargs.pop("stop")

        return kwargs


class CurrentTrackerCommand(TrackerCommand):
    """Retrieves and stores the current running tracker."""

    PREFIX = "current"
    ALIASES = ("now", "running")
    EXPIRATION = timedelta(seconds=10)
    ICON = APP_IMG

    __slots__ = ("_tracker", "_ts")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._ts: Optional[datetime] = None
        self._tracker: Optional[TogglTracker] = None

    def get_current_tracker(
        self,
        *,
        refresh: bool = False,
    ) -> Optional[TogglTracker]:
        if (
            self._ts is None
            or refresh
            or datetime.now(timezone.utc) - self.EXPIRATION >= self._ts
        ):
            self.tracker = super().get_current_tracker(refresh=True)
        return self.tracker

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        tracker = self.get_current_tracker()
        if tracker is None:
            return []
        return self.process_model(
            tracker,
            f"{self.prefix} {self.PREFIX}",
            alt_action=partial(
                self.call_pickle,
                "view",
                query=query,
                refresh=True,
                **kwargs,
            ),
            fmt_str="{name}",
        )

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        tracker = kwargs.get("model") or self.get_current_tracker(
            refresh=kwargs.get("refresh", False),
        )
        if tracker is None:
            return [
                QueryParameters(
                    TIP_IMAGES[TipSeverity.ERROR],
                    "Not Running!",
                    "No tracker is currently running!",
                    "tgl ",
                ),
            ]
        return self.process_model(
            tracker,
            partial(
                self.call_pickle,
                "handle",
                query=query,
                model=tracker,
                **kwargs,
            ),
            advanced=True,
            fmt_str="{name}",
        )

    @property
    def tracker(self) -> Optional[TogglTracker]:
        return self._tracker

    @tracker.setter
    def tracker(self, tracker: TogglTracker) -> None:
        self._tracker = tracker
        self._ts = datetime.now(timezone.utc)


class ListCommand(TrackerCommand):
    """List all trackers."""

    PREFIX = "list"
    ALIASES = ("ls", "lst")
    ICON = BROWSER_IMG

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                "View all your trackers.",
                f"{self.prefix} {self.PREFIX}",
                f"{self.prefix} {self.PREFIX} refresh",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        data: list[partial] = kwargs.get("data", [])
        if not data:
            kwargs["distinct"] = not kwargs.get("distinct", True)
            data = [
                partial(
                    self.process_model,
                    tracker,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=tracker,
                        **kwargs,
                    ),
                    fmt_str="{name}",
                )
                for tracker in self.get_models(**kwargs)
            ]

        return self.paginator(query, data, page=kwargs.get("page", 0))


class ContinueCommand(TrackerCommand):
    """Continue the last or selected tracker."""

    PREFIX = "continue"
    ALIASES = ("c", "cnt", "cont")
    ICON = CONTINUE_IMG
    ESSENTIAL = True

    def can_continue(self, **kwargs) -> bool:
        return not isinstance(
            self.current_tracker(
                refresh=kwargs.get("refresh", False),
            ),
            TogglTracker,
        )

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)

        if not self.can_continue(**kwargs):
            return []

        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                "Continue the last tracker.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        data: list[partial] = kwargs.get("data", [])
        if not self.can_continue(**kwargs):
            return [
                QueryParameters(
                    TIP_IMAGES[TipSeverity.ERROR],
                    "Error",
                    "A tracker is currently running!",
                    "tgl ",
                ),
            ]

        if not data:
            data = [
                partial(
                    self.process_model,
                    tracker,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=tracker,
                        **kwargs,
                    ),
                )
                for tracker in self.get_models(**kwargs)
            ]

        return self.paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        kwargs = self.sanitize_start_time(**kwargs)
        now = kwargs.get("start") or datetime.now(tz=timezone.utc)
        tracker = kwargs.get("model")

        if not isinstance(tracker, TogglTracker):
            user_endpoint = UserEndpoint(
                self.workspace_id,
                self.auth,
                self.cache,
            )
            if isinstance(tracker, int):
                tracker = user_endpoint.get_tracker(tracker)
            if tracker is None:
                start = datetime.now(tz=timezone.utc) - timedelta(days=7)
                tracker = user_endpoint.get_trackers(since=start, refresh=True)[0]

        if tracker is None:
            return False

        body = TrackerBody(
            self.workspace_id,
            tracker.name,
            duration=-1,
            project_id=tracker.project,
            start=now,
            tags=[t.name for t in tracker.tags],
            created_with="ulauncher-toggl-extension",
        )

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        cmd = CurrentTrackerCommand(self)
        cmd.tracker = endpoint.add_tracker(body)

        self.notification(msg=f"Continuing {tracker.name}!")

        return True

    def current_tracker(self, *, refresh: bool = False) -> Optional[TogglTracker]:
        cmd = CurrentTrackerCommand(self)
        return cmd.get_current_tracker(refresh=refresh)


class StartCommand(TrackerCommand):
    """Start a new tracker."""

    PREFIX = "start"
    ALIASES = ("stt", "begin")
    ICON = START_IMG

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                "Start a new tracker.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        cmp = self.autocomplete(query, **kwargs)
        data: list[partial] = kwargs.get("data", [])

        if not data:
            data = [
                partial(
                    self.process_model,
                    tracker,
                    self.generate_query(tracker),
                )
                for tracker in self.get_models(**kwargs)
            ]

        return self.paginator(
            query,
            cmp or data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, model: TogglTracker) -> str:
        query = f'{self.prefix} {self.PREFIX} "{model.name}"'
        now = datetime.now(tz=get_local_tz())
        query += f" >{now.strftime('%H:%M')}"
        if model.project:
            query += f" @{model.project}"

        if model.tags:
            query += f" #{','.join(tag.name for tag in model.tags)}"
        return query

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        kwargs = self.sanitize_start_time(**kwargs)
        now = datetime.now(tz=timezone.utc)
        tracker = kwargs.get("model")

        body = TrackerBody(
            self.workspace_id,
            kwargs.get("description", tracker.name if tracker else ""),
            project_id=kwargs.get("project", tracker.project if tracker else None),
            start=kwargs.get("start", now),
            tags=kwargs.get("tags")
            or ([t.name for t in tracker.tags] if tracker else []),
            created_with="ulauncher-toggl-extension",
        )

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        cmd = CurrentTrackerCommand(self)
        cmd.tracker = endpoint.add_tracker(body)

        self.notification(msg=f"Started new tracker {cmd.tracker.name}!")
        return True


class StopCommand(TrackerCommand):
    """Stop the tracker currently running!"""

    PREFIX = "stop"
    ALIASES = ("end", "stp")
    ICON = STOP_IMG

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)

        current_tracker = self.current_tracker(refresh=kwargs.get("refresh", False))
        if current_tracker is not None:
            return [
                QueryParameters(
                    self.ICON,
                    self.PREFIX.title(),
                    self.__doc__,
                    partial(
                        self.call_pickle,
                        method="handle",
                        model=current_tracker,
                        query=query,
                        **kwargs,
                    ),
                    f"{self.prefix} {self.PREFIX}",
                ),
            ]
        return []

    def current_tracker(self, *, refresh: bool = False) -> Optional[TogglTracker]:
        cmd = CurrentTrackerCommand(self)
        return cmd.get_current_tracker(refresh=refresh)

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        current_tracker = kwargs.get("model") or self.current_tracker()
        if current_tracker is None:
            return [
                QueryParameters(
                    TIP_IMAGES[TipSeverity.ERROR],
                    "Error",
                    "No tracker is currently running!",
                    "tgl ",
                ),
            ]
        kwargs["model"] = current_tracker
        handle = partial(
            self.call_pickle,
            method="handle",
            query=query,
            **kwargs,
        )
        results: list[QueryParameters] = [
            self.process_model(current_tracker, handle)[0],
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                handle,
                small=True,
            ),
        ]

        return results

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        current_tracker = kwargs.get("model")
        if not isinstance(current_tracker, TogglTracker):
            return False
        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            endpoint.stop_tracker(current_tracker)
        except HTTPStatusError as err:
            if err.response.status_code == endpoint.NOT_FOUND:
                self.notification(msg="Tracker does not exist anymore!")
                return True
            raise
        cmd = CurrentTrackerCommand(self)
        cmd.tracker = None
        self.notification(msg=f"Stopped {current_tracker.name}!")
        return True


class AddCommand(TrackerCommand):
    """Add a new tracker."""

    PREFIX = "add"
    ALIASES = ("a", "insert")
    ICON = ADD_IMG

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                "Add a new tracker.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        cmp = self.autocomplete(query, **kwargs)
        data: list[partial] = kwargs.get("data", [])

        if not data:
            data = [
                partial(
                    self.process_model,
                    tracker,
                    self.generate_query(tracker),
                )
                for tracker in self.get_models(**kwargs)
            ]

        return self.paginator(
            query,
            cmp or data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, model: TogglTracker) -> str:
        query = f'{self.prefix} {self.PREFIX} "{model.name}"'
        now = datetime.now(tz=get_local_tz())
        query += f" >{now.strftime('%H:%M')}"
        now += timedelta(hours=1)
        query += f" <{now.strftime('%H:%M')}"

        if model.project:
            query += f" @{model.project}"
        if model.tags:
            query += f" #{','.join(tag.name for tag in model.tags)}"
        return query

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        now = datetime.now(tz=timezone.utc)
        tags = kwargs.get("tags")
        body = TrackerBody(
            self.workspace_id,
            kwargs.get("description", ""),
            project_id=kwargs.get("project"),
            start=kwargs.get("start", now),
            stop=kwargs.get("stop"),
            tags=tags,
            tag_action="add",
            created_with="ulauncher-toggl-extension",
        )

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        tracker = endpoint.add_tracker(body)
        self.notification(msg=f"Created new tracker {tracker.name}!")
        return True


class EditCommand(TrackerCommand):
    """Edit a tracker."""

    PREFIX = "edit"
    ALIASES = ("ed", "change", "amend")
    ICON = EDIT_IMG
    ESSENTIAL = True

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                "Edit a tracker.",
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        cmp = self.autocomplete(query, **kwargs)
        data: list[partial] = kwargs.get("data", [])

        if not data:
            kwargs["distinct"] = not kwargs.get("distinct", True)
            data = [
                partial(
                    self.process_model,
                    tracker,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=tracker,
                        **kwargs,
                    ),
                    self.generate_query(tracker),
                )
                for tracker in self.get_models(**kwargs)
            ]

        return self.paginator(
            query,
            cmp or data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, model: TogglTracker) -> str:
        query = f'{self.prefix} {self.PREFIX} "{model.name}"'
        if model.project:
            query += f" @{model.project}"
        if model.start:
            query += f" >{model.start}"
        if model.stop:
            query += f" <{model.stop}"
        if model.tags:
            query += f" #{','.join(tag.name for tag in model.tags)}"
        return query

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        tracker = kwargs.get("model")
        if tracker is None:
            return False

        tags = kwargs.get("tags", [])
        body = TrackerBody(
            self.workspace_id,
            kwargs.get("description"),
            project_id=kwargs.get("project"),
            start=kwargs.get("start"),
            stop=kwargs.get("stop"),
            tags=tags,
            created_with="ulauncher-toggl-extension",
        )

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        tracker = endpoint.edit_tracker(tracker, body)
        self.notification(msg=f"Changed tracker {tracker.name}!")
        return True


class DeleteCommand(TrackerCommand):
    """Delete a tracker."""

    PREFIX = "delete"
    ALIASES = ("rm", "del", "remove")
    ICON = DELETE_IMG
    ESSENTIAL = True

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                "Delete a tracker.",
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        data: list[partial] = kwargs.get("data", [])

        if not data:
            kwargs["distinct"] = not kwargs.get("distinct", True)
            data = [
                partial(
                    self.process_model,
                    tracker,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=tracker,
                        **kwargs,
                    ),
                )
                for tracker in self.get_models(**kwargs)
            ]

        return self.paginator(query, data, page=kwargs.get("page", 0))

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        tracker = kwargs.get("model")
        if tracker is None:
            return False
        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        endpoint.delete_tracker(tracker)
        self.notification(msg=f"Removed {tracker.name}!")
        return True
