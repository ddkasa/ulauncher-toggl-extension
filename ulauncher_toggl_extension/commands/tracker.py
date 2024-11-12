from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import TYPE_CHECKING, Any, Literal, Optional

from httpx import HTTPStatusError
from toggl_api import (
    JSONCache,
    TogglProject,
    TogglQuery,
    TogglTracker,
    TrackerBody,
    TrackerEndpoint,
    UserEndpoint,
)

from ulauncher_toggl_extension.date_time import display_dt, format_seconds, get_local_tz
from ulauncher_toggl_extension.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    CONTINUE_IMG,
    DELETE_IMG,
    EDIT_IMG,
    REFRESH_IMG,
    START_IMG,
    STOP_IMG,
    TIP_IMAGES,
    TipSeverity,
)
from ulauncher_toggl_extension.utils import get_distance, quote_member

from .meta import ACTION_TYPE, ActionEnum, Command, QueryResults
from .project import ProjectCommand
from .tag import TagCommand

if TYPE_CHECKING:
    from pathlib import Path

    from ulauncher_toggl_extension.query import Query


log = logging.getLogger(__name__)


class TrackerCommand(Command[TogglTracker]):
    """Base Tracker command setting up default methods."""

    def process_model(
        self,
        model: TogglTracker,
        action: ACTION_TYPE,
        alt_action: Optional[ACTION_TYPE] = None,
        *,
        advanced: bool = False,
        fmt_str: str = "{prefix} {name}",
    ) -> list[QueryResults]:
        model_name = quote_member(self.PREFIX, model.name)
        name = fmt_str.format(prefix=self.PREFIX.title(), name=model_name)

        cmd = ProjectCommand(self)
        project = cmd.get_model(model.project)
        path = self.get_icon(project)
        description = f"@{project.name if project else model.project}" or ""
        if model.tags:
            description += f" #{','.join(tag.name for tag in model.tags)}"

        queries = [
            QueryResults(
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
                if isinstance(model.duration, timedelta)
                else datetime.now(timezone.utc) - model.start
            )

            extra = [
                QueryResults(
                    START_IMG,
                    dates[0],
                    "",
                    on_enter=ActionEnum.DO_NOTHING,
                    small=True,
                ),
                QueryResults(
                    APP_IMG,
                    f"Duration: {format_seconds(int(total_time.total_seconds()))}",
                    on_enter=ActionEnum.DO_NOTHING,
                    small=True,
                ),
            ]

            if dates[1]:
                extra.insert(
                    1,
                    QueryResults(
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
        if not isinstance(model.stop, datetime):
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

    def get_models(self, query: Query, **kwargs: Any) -> list[TogglTracker]:
        """Collects trackers and filters and sorts them for further use."""
        user = UserEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            trackers = user.collect(
                kwargs.get("since"),
                kwargs.get("before"),
                kwargs.get("end_date"),
                kwargs.get("start_date"),
                refresh=query.refresh,
            )
        except ValueError as err:
            self.handle_error(err)
            trackers = user.collect(query.refresh)
        except HTTPStatusError as err:
            self.handle_error(err)
            trackers = user.collect(
                kwargs.get("since"),
                kwargs.get("before"),
                kwargs.get("end_date"),
                kwargs.get("start_date"),
            )
        if isinstance(query.id, int):
            trackers.sort(
                key=lambda x: get_distance(query.id, x.id),
                reverse=query.sort_order,
            )
        elif isinstance(query.id, str):
            trackers.sort(
                key=lambda x: get_distance(query.id, x.name),
                reverse=query.sort_order,
            )
        else:
            trackers.sort(
                key=lambda x: (x.stop or datetime.now(tz=timezone.utc), x.start),
                reverse=query.sort_order,
            )
        if query.distinct:
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

    def get_current_tracker(self, *, refresh: bool = True) -> TogglTracker | None:
        user = UserEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            return user.current(refresh=refresh)
        except HTTPStatusError as err:
            self.handle_error(err)

        return None

    def autocomplete(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        raw_args = query.raw_args.copy()
        autocomplete: list[QueryResults] = []
        if not self.check_autocmp(raw_args):
            return autocomplete

        if raw_args[-1][0] == '"' and raw_args[-1][-1] != '"':
            pcmd = ProjectCommand(self)
            models = self.get_models(query, **kwargs)

            for tracker in models:
                raw_args[-1] = f'"{tracker.name}"'
                project = pcmd.get_model(tracker.project)
                autocomplete.append(
                    QueryResults(
                        self.get_icon(project),
                        tracker.name,
                        "Use this tracker description.",
                        " ".join(raw_args),
                    ),
                )

        elif raw_args[-1][0] == "@" and len(raw_args[-1]) < 4:  # noqa: PLR2004
            pcmd = ProjectCommand(self)

            for project in pcmd.get_models(query, **kwargs):
                raw_args[-1] = f'@"{project.name}"'
                autocomplete.append(
                    QueryResults(
                        pcmd.get_icon(project),
                        project.name,
                        "Use this project.",
                        " ".join(raw_args),
                    ),
                )

        elif raw_args[-1][0] == "#" and (
            len(raw_args[-1]) < 3 or raw_args[-1][-1] == ","  # noqa: PLR2004
        ):
            tcmd = TagCommand(self)

            for tag in tcmd.get_models(query, **kwargs):
                if "," in raw_args[-1]:
                    raw_args[-1] = (
                        raw_args[-1][: raw_args[-1].rfind(",")] + f",{tag.name}"
                    )
                else:
                    raw_args[-1] = f"#{tag.name}"
                autocomplete.append(
                    QueryResults(
                        tcmd.ICON,
                        tag.name,
                        "Use this tag.",
                        " ".join(raw_args),
                    ),
                )

        autocomplete.sort(
            key=lambda x: get_distance(query.raw_args[-1][1:], x.name),
            reverse=True,
        )

        return autocomplete

    @property
    def cache(self) -> JSONCache[TogglTracker]:
        return JSONCache(self.cache_path, self.expiration)

    def handle(self, query: Query, **kwargs: Any) -> bool | list[QueryResults]:
        handle = super().handle(query, **kwargs)
        if not isinstance(handle, list):
            return handle
        model: TogglTracker = kwargs.get("model")
        if model.running():
            handle.pop(3)
        elif CurrentTrackerCommand(self).get_current_tracker() is not None:
            handle.pop(4)
        return handle

    def get_model(
        self,
        model_id: TogglTracker | int | str | None,
        *,
        refresh: bool = True,
    ) -> TogglTracker | None:
        if model_id is None or isinstance(model_id, TogglTracker):
            return model_id

        endpoint = UserEndpoint(self.workspace_id, self.auth, self.cache)

        if isinstance(model_id, str):
            model = list(endpoint.query(TogglQuery("name", model_id), distinct=True))
            if model:
                return model[0]
            return None

        return endpoint.get(model_id, refresh=refresh)


class CurrentTrackerCommand(TrackerCommand):
    """Retrieves and stores the current running tracker."""

    PREFIX = "current"
    ALIASES = ("now", "running")
    EXPIRATION = timedelta(seconds=10)
    ICON = APP_IMG
    OPTIONS = ("refresh",)

    __slots__ = ("_tracker", "_ts")

    def __init__(self, *args, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._ts: Optional[datetime] = None
        self._tracker: Optional[TogglTracker] = None

    def get_current_tracker(self, *, refresh: bool = False) -> TogglTracker | None:
        if (
            self._ts is None
            or refresh
            or datetime.now(timezone.utc) - self.EXPIRATION >= self._ts
        ):
            self.tracker = super().get_current_tracker(refresh=True)
        return self.tracker

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
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
            fmt_str="Current: {name}",
        )

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        tracker = kwargs.get("model") or self.get_current_tracker(
            refresh=query.refresh,
        )
        if tracker is None:
            return [
                QueryResults(
                    TIP_IMAGES[TipSeverity.ERROR],
                    "Not Running!",
                    "No tracker is currently running!",
                    "tgl ",
                ),
            ]
        kwargs["model"] = tracker

        details = self.process_model(
            tracker,
            partial(
                self.call_pickle,
                "handle",
                query=query,
                **kwargs,
            ),
            advanced=True,
            fmt_str="{name}",
        )
        details.append(
            QueryResults(
                StopCommand.ICON,
                f"Stop {tracker.name}",
                on_enter=partial(StopCommand(self).handle, query, **kwargs),
                small=True,
            ),
        )
        return details

    def handle(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        result: list[QueryResults] = super().handle(query, **kwargs)  # type: ignore[assignment]
        model = self.get_current_tracker()
        if not model:
            return result

        result.append(
            QueryResults(
                StopCommand.ICON,
                f"Stop {model.name}",
                on_enter=partial(StopCommand(self).handle, query, **kwargs),
                small=True,
            ),
        )
        return result

    @property
    def tracker(self) -> TogglTracker | None:
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

    OPTIONS = ("refresh", "distinct", "^-", ":")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                "View all your trackers.",
                f"{self.prefix} {self.PREFIX}",
                f"{self.prefix} {self.PREFIX} refresh",
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        if query.id:
            kwargs["model"] = self.get_model(query.id, refresh=query.refresh)
            if kwargs["model"]:
                return self.handle(query, **kwargs)  # type: ignore[return-value]

        data: list[partial] = kwargs.get("data", [])
        if not data:
            query.distinct = not query.distinct
            data = [
                partial(
                    self.process_model,
                    tracker,
                    f"{self.prefix} {self.PREFIX} :{tracker.id}",
                    fmt_str="{name}",
                )
                for tracker in self.get_models(query, **kwargs)
            ]

        return self._paginator(query, data, page=kwargs.get("page", 0))


class ContinueCommand(TrackerCommand):
    """Continue the last or selected tracker."""

    PREFIX = "continue"
    ALIASES = ("cnt", "restart", "cont")
    ICON = CONTINUE_IMG
    ESSENTIAL = True

    OPTIONS = ("refresh", "distinct", ">", "^-", ":")

    def can_continue(self, *, refresh: bool = False) -> bool:
        return not isinstance(
            self.current_tracker(refresh=refresh),
            TogglTracker,
        )

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)

        if not self.can_continue(
            refresh=query.refresh,
        ) or not self.get_models(query, **kwargs):
            return []

        return [
            QueryResults(
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

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        data: list[partial] = kwargs.get("data", [])
        if not self.get_models(query, **kwargs):
            return [
                QueryResults(
                    TIP_IMAGES[TipSeverity.ERROR],
                    "Error",
                    "No trackers are available!",
                    "tgl ",
                ),
            ]
        if not self.can_continue(refresh=query.refresh):
            return [
                QueryResults(
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
                for tracker in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def handle(self, query: Query, **kwargs: Any) -> bool:
        now = query.start or datetime.now(tz=timezone.utc)
        tracker = kwargs.get("model", query.id)

        if not isinstance(tracker, TogglTracker):
            if isinstance(tracker, int | str):
                tracker = self.get_model(tracker)

            if tracker is None:
                query.sort_order = True
                tracker = self.get_models(query, refresh=query.refresh)

                if not tracker:
                    msg = "No recent trackers available!"
                    log.warning(msg)
                    self.notification(msg)
                    return False
                tracker = tracker[0]

        if tracker is None:
            return False

        body = TrackerBody(
            tracker.name,
            duration=-1,
            project_id=tracker.project,
            start=now,
            tags=[t.name for t in tracker.tags],
            created_with="ulauncher-toggl-extension",
        )

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        cmd = CurrentTrackerCommand(self)
        try:
            cmd.tracker = endpoint.add(body)
        except (HTTPStatusError, TypeError) as err:
            self.handle_error(err)
        else:
            self.notification(msg=f"Continuing {tracker.name}!")
            return True
        return False

    def current_tracker(self, *, refresh: bool = False) -> TogglTracker | None:
        cmd = CurrentTrackerCommand(self)
        return cmd.get_current_tracker(refresh=refresh)


class StartCommand(TrackerCommand):
    """Start a new tracker."""

    PREFIX = "start"
    ALIASES = ("stt", "begin")
    ICON = START_IMG
    OPTIONS = ("refresh", "distinct", ">", '"', "@", "#")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        return [
            QueryResults(
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

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        cmp = self.autocomplete(query, **kwargs)
        data: list[partial] = kwargs.get("data", [])

        if not data:
            data = [
                partial(
                    self.process_model,
                    tracker,
                    self.generate_query(tracker),
                )
                for tracker in self.get_models(query, **kwargs)
            ]

        return self._paginator(
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

    def handle(self, query: Query, **_: Any) -> bool:
        now = datetime.now(tz=timezone.utc)

        project = self.get_model(query.project)
        body = TrackerBody(
            query.name,
            project_id=project.id if project else None,
            start=query.start or now,
            tags=query.add_tags,
            created_with="ulauncher-toggl-extension",
        )

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        cmd = CurrentTrackerCommand(self)

        try:
            cmd.tracker = endpoint.add(body)
        except (HTTPStatusError, TypeError) as err:
            self.handle_error(err)
        else:
            if not cmd.tracker:
                return False
            self.notification(msg=f"Started new tracker {cmd.tracker.name}!")
            return True

        return False


class StopCommand(TrackerCommand):
    """Stop the tracker currently running!"""

    PREFIX = "stop"
    ALIASES = ("end", "stp")
    ICON = STOP_IMG
    OPTIONS = ("refresh", "distinct", "<")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)

        current_tracker = self.current_tracker(refresh=query.refresh)
        if current_tracker is not None:
            return [
                QueryResults(
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

    def current_tracker(self, *, refresh: bool = False) -> TogglTracker | None:
        cmd = CurrentTrackerCommand(self)
        return cmd.get_current_tracker(refresh=refresh)

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        current_tracker = kwargs.get("model") or self.current_tracker()
        if current_tracker is None:
            return [
                QueryResults(
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

        results: list[QueryResults] = self.process_model(
            current_tracker,
            handle,
            advanced=True,
        )[0:3]

        results.append(
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                handle,
                small=True,
            ),
        )

        return results

    def handle(self, query: Query, **kwargs: Any) -> bool:
        current_tracker = kwargs.get("model")
        if not isinstance(current_tracker, TogglTracker):
            return False
        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        cmd = CurrentTrackerCommand(self)

        try:
            current_tracker = endpoint.stop(current_tracker) or current_tracker
            if isinstance(query.stop, datetime) and query.stop > current_tracker.start:
                body = TrackerBody(stop=query.stop)
                endpoint.edit(current_tracker, body)
        except HTTPStatusError as err:
            self.handle_error(err)
        else:
            cmd.tracker = None
            self.notification(msg=f"Stopped {current_tracker.name}!")
            return True
        return False


class AddCommand(TrackerCommand):
    """Add a new tracker."""

    PREFIX = "add"
    ALIASES = ("create", "insert")
    ICON = ADD_IMG
    OPTIONS = ("refresh", "distinct", ">", '"', "@", "#", "<")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        return [
            QueryResults(
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

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        cmp = self.autocomplete(query, **kwargs)
        data: list[partial] = kwargs.get("data", [])

        if not data:
            data = [
                partial(
                    self.process_model,
                    tracker,
                    self.generate_query(tracker),
                )
                for tracker in self.get_models(query, **kwargs)
            ]

        return self._paginator(
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

    def handle(self, query: Query, **kwargs: Any) -> bool:
        del kwargs
        now = datetime.now(tz=timezone.utc)

        project = ProjectCommand(self).get_model(
            query.project,
            refresh=query.refresh,
        )

        body = TrackerBody(
            query.name,
            project_id=project.id if project else None,
            start=query.start or now,
            stop=query.stop,
            tags=query.add_tags,
            tag_action="add",
            created_with="ulauncher-toggl-extension",
        )

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            tracker = endpoint.add(body)
        except (HTTPStatusError, TypeError) as err:
            self.handle_error(err)
        else:
            if tracker is None:
                return False
            self.notification(msg=f"Created new tracker {tracker.name}!")
            return True

        return False


class EditCommand(TrackerCommand):
    """Edit a tracker."""

    PREFIX = "edit"
    ALIASES = ("ed", "change", "amend")
    ICON = EDIT_IMG
    ESSENTIAL = True

    OPTIONS = ("refresh", "distinct", ">", "<", '"', "@", "#")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                "Edit a tracker.",
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        cmp = self.autocomplete(query, **kwargs)
        data: list[partial] = kwargs.get("data", [])

        if not data:
            query.distinct = not query.distinct
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
                for tracker in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            cmp or data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, model: TogglTracker) -> str:
        query = f'{self.prefix} {self.PREFIX} "{model.name}"'
        if model.project:
            query += f' @"{model.project}"'
        if model.start:
            query += f" >{model.start.strftime('%Y-%m-%dT%H:%M')}"
        if isinstance(model.stop, datetime):
            query += f" <{model.stop.strftime('%Y-%m-%dT%H:%M')}"
        if model.tags:
            query += f" #{','.join(tag.name for tag in model.tags)}"
        return query

    def handle(self, query: Query, **kwargs: Any) -> bool:
        tracker = kwargs.get("model", query.id)

        if isinstance(tracker, str):
            tracker = self.get_model(tracker)

        if tracker is None:
            return False

        project = ProjectCommand(self).get_model(
            query.project,
            refresh=query.refresh,
        )

        body = TrackerBody(
            query.name,
            project_id=project.id if project else None,
            start=query.start,
            stop=query.stop,
            tags=query.add_tags or query.rm_tags,
            tag_action="add" if query.add_tags else "remove",
            created_with="ulauncher-toggl-extension",
        )

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)

        try:
            tracker = endpoint.edit(tracker, body)
            if query.add_tags or query.rm_tags:
                body = TrackerBody(tags=query.rm_tags, tag_action="remove")
                tracker = endpoint.edit(tracker, body)

        except HTTPStatusError as err:
            self.handle_error(err)
        else:
            if tracker is None:
                return False
            self.notification(msg=f"Changed tracker {tracker.name}!")
            return True

        return False


class DeleteCommand(TrackerCommand):
    """Delete a tracker."""

    PREFIX = "delete"
    ALIASES = ("rm", "del", "remove")
    ICON = DELETE_IMG
    ESSENTIAL = True
    OPTIONS = ("refresh", "distinct", ":")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                "Delete a tracker.",
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        data: list[partial] = kwargs.get("data", [])

        if not data:
            query.distinct = not query.distinct
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
                for tracker in self.get_models(query, **kwargs)
            ]

        return self._paginator(query, data, page=kwargs.get("page", 0))

    def handle(self, query: Query, **kwargs: Any) -> bool:
        tracker = kwargs.get("model", query.id)

        if isinstance(tracker, str):
            tracker = self.get_model(tracker)

        if tracker is None:
            return False

        endpoint = TrackerEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            endpoint.delete(tracker)
        except HTTPStatusError as err:
            self.handle_error(err)
        else:
            current_cmd = CurrentTrackerCommand(self)
            current_tracker = current_cmd.get_current_tracker()
            if current_tracker and tracker.id == current_tracker.id:
                current_cmd.tracker = None
            self.notification(msg=f"Removed {tracker.name}!")
            return True

        return False


class RefreshCommand(TrackerCommand):
    """Refresh specific trackers."""

    PREFIX = "refresh"
    ALIASES = ("re", "update")
    ICON = REFRESH_IMG
    ESSENTIAL = True

    OPTIONS = ("refresh", "distinct", "->")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:  # noqa: PLR6301
        del query, kwargs
        return []

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        data: list[partial] = kwargs.get("data", [])
        if not data:
            query.distinct = not query.distinct

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
                for tracker in self.get_models(query, **kwargs)
            ]

        return self._paginator(query, data, page=kwargs.get("page", 0))

    def handle(self, query: Query, **kwargs: Any) -> Literal[False]:
        model = kwargs.get("model", query.id)
        if isinstance(model, str):
            model = self.get_model(model, refresh=query.refresh)

        if model is None:
            return False

        endpoint = UserEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            model = endpoint.get(model, refresh=True)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        if model is None:
            return False

        self.notification(f"Successfully refreshed tracker '{model.name}'!")

        return False
