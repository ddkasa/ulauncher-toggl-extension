from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any, Literal, Optional

from httpx import HTTPStatusError
from toggl_api import ProjectBody, ProjectEndpoint, TogglProject, TogglQuery

from ulauncher_toggl_extension.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    CIRCULAR_SVG,
    DELETE_IMG,
    EDIT_IMG,
    REFRESH_IMG,
)
from ulauncher_toggl_extension.utils import quote_member

from .client import ClientCommand
from .meta import ACTION_TYPE, QueryResults, SubCommand

if TYPE_CHECKING:
    from pathlib import Path

    from ulauncher_toggl_extension.query import Query

log = logging.getLogger(__name__)


class ProjectCommand(SubCommand[TogglProject]):
    """Subcommand for all project based tasks."""

    PREFIX = "project"
    ALIASES = ("p", "proj")
    ICON = APP_IMG  # TODO: Need a custom image
    EXPIRATION = None
    OPTIONS = ()

    def process_model(
        self,
        model: TogglProject,
        action: ACTION_TYPE,
        alt_action: Optional[ACTION_TYPE] = None,
        *,
        advanced: bool = False,
        fmt_str: str = "{prefix} {name}",
    ) -> list[QueryResults]:
        cmd = ClientCommand(self)
        client = cmd.get_model(model.client)

        model_name = quote_member(self.PREFIX, model.name)
        results = [
            QueryResults(
                self.get_icon(model),
                fmt_str.format(prefix=self.PREFIX.title(), name=model_name),
                f"${client.name if client else model.client}" if model.client else "",
                action,
                alt_action,
            ),
        ]

        if advanced:
            results.extend(
                (
                    QueryResults(
                        self.ICON,
                        f"{model.name} is{' not' if not model.active else ''} active.",
                        "",
                        small=True,
                    ),
                    QueryResults(
                        self.get_icon(model),
                        "Color",
                        model.color,
                        small=True,
                    ),
                ),
            )

        return results

    def get_models(self, query: Query, **kwargs: Any) -> list[TogglProject]:
        del kwargs
        user = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            projects = user.collect(refresh=query.refresh)
        except HTTPStatusError as err:
            self.handle_error(err)
            return []

        if query.active:
            projects = [project for project in projects if project.active]

        projects.sort(key=lambda x: x.timestamp, reverse=query.sort_order)
        return projects

    def get_model(
        self,
        project_id: Optional[int | str | TogglProject] = None,
        *,
        refresh: bool = False,
    ) -> TogglProject | None:
        if project_id is None or isinstance(project_id, TogglProject):
            return project_id

        endpoint = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        if isinstance(project_id, str):
            project = list(endpoint.query(TogglQuery("name", project_id)))
            return project[0] if project else None

        try:
            return endpoint.get(project_id, refresh=refresh)
        except HTTPStatusError as err:
            self.handle_error(err)
            return None

    def autocomplete(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        raw_args = query.raw_args.copy()
        autocomplete: list[QueryResults] = []
        if not self.check_autocmp(raw_args):
            return autocomplete

        if raw_args[-1][0] == '"' and raw_args[-1][-1] != '"':
            models = self.get_models(query, **kwargs)

            for model in models:
                raw_args[-1] = f'"{model.name}"'
                autocomplete.append(
                    QueryResults(
                        self.get_icon(model),
                        model.name,
                        "Use this project name.",
                        " ".join(raw_args),
                    ),
                )

        elif raw_args[-1][0] == "#" and len(raw_args[-1]) < 6:  # noqa: PLR2004
            path = self.cache_path / "svg"
            path.mkdir(parents=True, exist_ok=True)
            for name, color in ProjectEndpoint.BASIC_COLORS.items():
                raw_args[-1] = f"{color}"
                icon = path / f"{color}.svg"
                if not icon.exists():
                    self.create_color(icon, color)
                autocomplete.append(
                    QueryResults(
                        icon,
                        name.title(),
                        color,
                        " ".join(raw_args),
                    ),
                )

        elif raw_args[-1][0] == "$" and len(raw_args[-1]) < 3:  # noqa: PLR2004
            cmd = ClientCommand(self)

            for model in cmd.get_models(query, **kwargs):
                raw_args[-1] = f'$"{model.name}"'
                autocomplete.append(
                    QueryResults(
                        cmd.ICON,
                        model.name,
                        "Use this client.",
                        " ".join(raw_args),
                    ),
                )

        return autocomplete

    def get_icon(self, project: Optional[TogglProject] = None) -> Path:
        if project is None or not project.color:
            return self.ICON

        return self.generate_color_svg(project)

    @staticmethod
    def create_color(path: Path, color: str) -> None:
        svg = CIRCULAR_SVG.format(color=color)
        with path.open("w", encoding="utf-8") as file:
            file.write(svg)

    def generate_color_svg(self, project: TogglProject) -> Path:
        path = self.cache_path / "svg"
        path.mkdir(parents=True, exist_ok=True)
        icon = path / f"{project.color}.svg"

        if icon.exists():
            return icon

        log.debug("Creating SVG colored circle %s at %s.", project.color, icon)
        self.create_color(icon, project.color)

        return path


class ListProjectCommand(ProjectCommand):
    """List all projects."""

    PREFIX = "list"
    ALIASES = ("ls", "l")
    ICON = BROWSER_IMG
    OPTIONS = ("refresh", ":")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                "List Projects.",
                self.get_cmd(),
                self.get_cmd() + " refresh",
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        if query.id:
            kwargs["model"] = self.get_model(query.id)
            if kwargs["model"]:
                return self.handle(query, **kwargs)  # type: ignore[return-value]

        self.amend_query(query.raw_args)
        data: list[partial] = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    project,
                    self.get_cmd() + f' :"{project.id}"',
                    fmt_str="{name}",
                )
                for project in self.get_models(query, **kwargs)
            ]

        return self._paginator(query, data, page=kwargs.get("page", 0))


class AddProjectCommand(ProjectCommand):
    """Create a new project."""

    PREFIX = "add"
    ALIASES = ("a", "create", "insert")
    ICON = ADD_IMG
    OPTIONS = ("refresh", "#", "$", '"', ">", "<")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                "Add a new project.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
                self.get_cmd(),
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        cmp = self.autocomplete(query, **kwargs)
        data = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    project,
                    self.generate_query(project),
                )
                for project in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            cmp or data,
            self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, project: TogglProject) -> str:
        query = self.get_cmd()

        if project.name:
            query += f' "{project.name}"'
        if project.client:
            query += f" ${project.client}"
        if project.color:
            query += f" #{project.color}"
        return query

    def handle(self, query: Query, **kwargs: Any) -> bool:
        del kwargs
        if not query.name:
            return False

        body = ProjectBody(
            name=query.name,
            active=query.active,
            client_id=query.client if isinstance(query.client, int) else None,
            client_name=query.client if isinstance(query.client, str) else None,
            is_private=query.private,
            color=query.color,
            start_date=query.start,
            end_date=query.stop,
        )

        endpoint = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            proj = endpoint.add(body)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        if proj is None:
            return False

        self.notification(msg=f"Created project {body.name}!")

        return True


class EditProjectCommand(ProjectCommand):
    """Edit a project."""

    PREFIX = "edit"
    ALIASES = ("e", "change", "amend")
    ICON = EDIT_IMG
    ESSENTIAL = True
    OPTIONS = ("refresh", "#", "$", '"', ":")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        cmp = self.autocomplete(query, **kwargs)
        data = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    project,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=project,
                        **kwargs,
                    ),
                    self.generate_query(project),
                )
                for project in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            cmp or data,
            self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, project: TogglProject) -> str:
        query = self.get_cmd() + f' "{project.name}"'
        if project.client:
            query += f" ${project.client}"
        return query

    def handle(self, query: Query, **kwargs: Any) -> bool:
        endpoint = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        model = kwargs.get("model") or self.get_model(query.id)
        if not isinstance(model, TogglProject | int):
            return False

        body = ProjectBody(
            name=query.name,
            active=query.active,
            client_id=query.client if isinstance(query.client, int) else None,
            client_name=query.client if isinstance(query.client, str) else None,
            is_private=query.private,
            color=query.color,
            start_date=query.start,
            end_date=query.stop,
        )
        if isinstance(model, int):
            model = TogglProject(model, "")

        try:
            proj = endpoint.edit(model, body)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        if proj is None:
            return False

        self.notification(msg=f"Edited project {body.name}!")

        return True


class DeleteProjectCommand(ProjectCommand):
    """Delete a project."""

    PREFIX = "delete"
    ALIASES = ("rm", "d", "del")
    ICON = DELETE_IMG
    ESSENTIAL = True
    OPTIONS = ("refresh", ":", "^-")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        cmp = self.autocomplete(query, **kwargs)
        data = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    project,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=project,
                        **kwargs,
                    ),
                )
                for project in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            cmp or data,
            self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, project: TogglProject) -> str:
        query = self.get_cmd()
        if project.name:
            query += f' "{project.name}"'

        return query

    def handle(self, query: Query, **kwargs: Any) -> bool:
        endpoint = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        model = kwargs.get("model") or self.get_model(query.id)
        if not isinstance(model, TogglProject | int):
            return False

        if isinstance(model, int):
            model = TogglProject(model, "")

        try:
            endpoint.delete(model)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        self.notification(msg=f"Deleted project {model.name}!")

        return True


class RefreshProjectCommand(ProjectCommand):
    """Refresh specific projects."""

    PREFIX = "refresh"
    ALIASES = ("re", "update")
    ICON = REFRESH_IMG
    ESSENTIAL = True

    OPTIONS = ("refresh", "distinct", ":", "^-")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:  # noqa: PLR6301
        del query, kwargs
        return []

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        data: list[partial] = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    project,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=project,
                        **kwargs,
                    ),
                    fmt_str="{name}",
                )
                for project in self.get_models(query, **kwargs)
            ]

        return self._paginator(query, data, page=kwargs.get("page", 0))

    def handle(self, query: Query, **kwargs: Any) -> Literal[False]:
        model = kwargs.get("model") or query.id
        if isinstance(model, str):
            model = self.get_model(model)

        if model is None:
            return False

        model = self.get_model(model, refresh=True)
        if model is None:
            return False

        self.notification(f"Successfully refreshed project '{model.name}'!")

        return False
