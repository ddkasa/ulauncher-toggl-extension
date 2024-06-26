from __future__ import annotations

import logging
from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING, Optional

from toggl_api import ProjectBody, ProjectEndpoint, TogglProject

from ulauncher_toggl_extension.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    CIRCULAR_SVG,
    DELETE_IMG,
    EDIT_IMG,
)

from .client import ClientCommand
from .meta import ACTION_TYPE, QueryParameters, SubCommand

if TYPE_CHECKING:
    from pathlib import Path

log = logging.getLogger(__name__)


class ProjectCommand(SubCommand):
    """Subcommand for all project based tasks."""

    PREFIX = "project"
    ALIASES = ("p", "proj")
    ICON = APP_IMG  # TODO: Need a custom image
    EXPIRATION = timedelta(weeks=1)

    def process_model(  # noqa: PLR0913
        self,
        model: TogglProject,
        action: ACTION_TYPE,
        alt_action: Optional[ACTION_TYPE] = None,
        *,
        advanced: bool = False,
        fmt_str: str = "{prefix} {name}",
    ) -> list[QueryParameters]:
        cmd = ClientCommand(self)
        client = cmd.get_client(model.client)
        results = [
            QueryParameters(
                self.get_icon(model),
                fmt_str.format(prefix=self.PREFIX.title(), name=model.name),
                f"${client.name if client else model.client}" if model.client else "",
                action,
                alt_action,
            ),
        ]

        if advanced:
            pass

        return results

    def get_models(self, **kwargs) -> list[TogglProject]:
        user = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        return user.get_projects(refresh=kwargs.get("refresh", False))

    def get_project(
        self,
        project_id: Optional[int] = None,
        *,
        refresh: bool = False,
    ) -> Optional[TogglProject]:
        if project_id is None:
            return None
        endpoint = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        return endpoint.get_project(project_id, refresh=refresh)

    def autocomplete(
        self,
        query: list[str],
        **kwargs,
    ) -> list[QueryParameters]:
        query = query.copy()
        query.insert(0, self.prefix)
        autocomplete: list[QueryParameters] = []
        if not self.check_autocmp(query):
            return autocomplete

        if query[-1][0] == '"':
            models = self.get_models(**kwargs)

            for model in models:
                query[-1] = f'"{model.name}"'
                autocomplete.append(
                    QueryParameters(
                        self.get_icon(model),
                        model.name,
                        "Use this project name.",
                        " ".join(query),
                    ),
                )

        elif query[-1][0] == "#":
            path = self.cache_path / "svg"
            path.mkdir(parents=True, exist_ok=True)
            for name, color in ProjectEndpoint.BASIC_COLORS.items():
                query[-1] = f"{color}"
                icon = path / f"{color}.svg"
                if not icon.exists():
                    self.create_color(icon, color)
                autocomplete.append(
                    QueryParameters(
                        icon,
                        name.title(),
                        color,
                        " ".join(query),
                    ),
                )

        elif query[-1][0] == "$":
            cmd = ClientCommand(self)

            for model in cmd.get_models(**kwargs):
                query[-1] = f"${model.id}"
                autocomplete.append(
                    QueryParameters(
                        cmd.ICON,
                        model.name,
                        "Use this client.",
                        " ".join(query),
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

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                "List Projects.",
                self.get_cmd(),
                self.get_cmd() + " refresh",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
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
                for project in self.get_models(**kwargs)
            ]

        return self.paginator(query, data, page=kwargs.get("page", 0))


class AddProjectCommand(ProjectCommand):
    """Create a new project."""

    PREFIX = "add"
    ALIASES = ("a", "create", "insert")
    ICON = ADD_IMG

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        return [
            QueryParameters(
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

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        cmp = self.autocomplete(query, **kwargs)
        data = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    project,
                    self.generate_query(project),
                )
                for project in self.get_models(**kwargs)
            ]

        return self.paginator(
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

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        name = kwargs.get("description")
        if name is None:
            return False
        endpoint = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        client = kwargs.get("client")
        color = kwargs.get("tags", [None])[0]
        if isinstance(color, str):
            color = "#" + color

        body = ProjectBody(
            self.workspace_id,
            name=name,
            active=kwargs.get("active", True),
            client_id=client if isinstance(client, int) else None,
            client_name=client if isinstance(client, str) else None,
            is_private=kwargs.get("private", True),
            color=color,
            start_date=kwargs.get("start"),
            end_date=kwargs.get("end_date"),
        )
        endpoint.add_project(body)

        self.notification(msg=f"Created project {body.name}!")

        return True


class EditProjectCommand(ProjectCommand):
    """Edit a project."""

    PREFIX = "edit"
    ALIASES = ("e", "change", "amend")
    ICON = EDIT_IMG
    ESSENTIAL = True

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        cmp = self.autocomplete(query, **kwargs)
        data = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    project,
                    self.generate_query(project),
                )
                for project in self.get_models(**kwargs)
            ]

        return self.paginator(
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

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        endpoint = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        model = kwargs.get("model") or kwargs.get("project")
        description = kwargs.get("description")
        if not isinstance(model, TogglProject | int):
            return False
        client = kwargs.get("client")

        body = ProjectBody(
            self.workspace_id,
            name=description if isinstance(description, str) else None,
            active=kwargs.get("active", True),
            client_id=client if isinstance(client, int) else None,
            client_name=client if isinstance(client, str) else None,
            is_private=kwargs.get("is_private", False),
            color=kwargs.get("color"),
            start_date=kwargs.get("start"),
            end_date=kwargs.get("end_date"),
        )
        if isinstance(model, int):
            model = TogglProject(model, "")
        endpoint.edit_project(model, body)

        self.notification(msg=f"Changed project {body.name}!")

        return True


class DeleteProjectCommand(ProjectCommand):
    """Delete a project."""

    PREFIX = "delete"
    ALIASES = ("rm", "d", "del")
    ICON = DELETE_IMG
    ESSENTIAL = True

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
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
                for project in self.get_models(**kwargs)
            ]

        return self.paginator(
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

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        endpoint = ProjectEndpoint(self.workspace_id, self.auth, self.cache)
        model = kwargs.get("model") or kwargs.get("project")
        if not isinstance(model, TogglProject | int):
            return False
        if isinstance(model, int):
            model = TogglProject(model, "")
        endpoint.delete_project(model)

        self.notification(msg=f"Deleted project {model.name}!")

        return True
