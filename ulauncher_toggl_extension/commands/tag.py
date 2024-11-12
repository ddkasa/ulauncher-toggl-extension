from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any

from httpx import HTTPStatusError
from toggl_api import TagEndpoint, TogglQuery, TogglTag

from ulauncher_toggl_extension.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    DELETE_IMG,
    EDIT_IMG,
)
from ulauncher_toggl_extension.utils import get_distance

from .meta import QueryResults, SubCommand

if TYPE_CHECKING:
    from ulauncher_toggl_extension.query import Query

log = logging.getLogger(__name__)


class TagCommand(SubCommand[TogglTag]):
    """Subcommand for all tag based tasks."""

    PREFIX = "tag"
    ALIASES = ("tags",)
    ICON = APP_IMG  # TODO: Need a custom image
    EXPIRATION = None
    OPTIONS = ()

    def get_models(self, query: Query, **_) -> list[TogglTag]:
        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            tags = endpoint.collect(refresh=query.refresh)
        except HTTPStatusError as err:
            self.handle_error(err)
            tags = endpoint.collect()
        if isinstance(query.id, int):
            tags.sort(
                key=lambda x: get_distance(query.id, x.id),
                reverse=query.sort_order,
            )
        elif isinstance(query.id, str):
            tags.sort(
                key=lambda x: get_distance(query.id, x.name),
                reverse=query.sort_order,
            )
        else:
            tags.sort(
                key=lambda x: x.timestamp,
                reverse=query.sort_order,
            )
        return tags

    def get_model(self, model: int | str | TogglTag | None) -> TogglTag | None:
        if model is None or isinstance(model, TogglTag):
            return model

        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)

        query = list(
            endpoint.query(
                TogglQuery("id" if isinstance(model, int) else "name", model),
                distinct=True,
            ),
        )
        if query:
            return query[0]

        return None


class ListTagCommand(TagCommand):
    """List all tags."""

    PREFIX = "list"
    ALIASES = ("ls", "lst")
    ICON = BROWSER_IMG
    OPTIONS = ("refresh", "^-")

    def preview(self, query: Query, **_) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
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
        data: list[QueryResults] = kwargs.get("data", [])
        if not data:
            for tag in self.get_models(query, **kwargs):
                mdl = self.process_model(
                    tag,
                    self.get_cmd() + f" :{tag.id}",
                    fmt_str="{name}",
                )
                data.append(mdl[0])

        return self._paginator(query, data, page=kwargs.get("page", 0))


class AddTagCommand(TagCommand):
    """Create a new tag."""

    PREFIX = "add"
    ALIASES = ("create", "insert")
    ICON = ADD_IMG
    OPTIONS = ("refresh", '"')

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
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
        data: list[partial] = kwargs.get("data", [])

        if not data:
            data = [
                partial(
                    self.process_model,
                    tag,
                    self.generate_query(tag),
                )
                for tag in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, model: TogglTag) -> str:
        query = self.get_cmd()
        if model.name:
            query += f' "{model.name}"'

        return query

    def handle(self, query: Query, **_) -> bool:
        if not isinstance(query.name, str):
            return False

        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            tag = endpoint.add(query.name)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        if not tag:
            return False

        self.notification(msg=f"Created a new tag: {query.name}!")
        return True


class EditTagCommand(TagCommand):
    """Edit an existing tag."""

    PREFIX = "edit"
    ALIASES = ("ed", "change", "amend")
    ICON = EDIT_IMG
    ESSENTIAL = True
    OPTIONS = ("refresh", '"', ":")

    def preview(self, query: Query, **_) -> list[QueryResults]:
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
        data: list[partial] = kwargs.get("data", [])

        if not data:
            data = [
                partial(
                    self.process_model,
                    tag,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=tag,
                        **kwargs,
                    ),
                    self.generate_query(tag),
                )
                for tag in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, model: TogglTag) -> str:
        query = self.get_cmd()
        if model.name:
            query += f' "{model.name}"'

        return query

    def handle(self, query: Query, **kwargs: Any) -> bool:
        model = self.get_model(kwargs.get("model", query.id))

        if not isinstance(model, TogglTag) or not isinstance(query.name, str):
            return False

        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)

        try:
            tag = endpoint.edit(model.id, query.name)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        if not tag:
            return False

        self.notification(f"Updated tag {model.name} with a new name {query.name}!")

        return True


class DeleteTagCommand(TagCommand):
    """Delete an existing tag."""

    PREFIX = "delete"
    ALIASES = ("rm", "del", "remove")
    ICON = DELETE_IMG
    ESSENTIAL = True
    OPTIONS = ("refresh",)

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
        data: list[partial] = kwargs.get("data", [])

        if not data:
            data = [
                partial(
                    self.process_model,
                    tag,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=tag,
                        **kwargs,
                    ),
                )
                for tag in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def handle(self, query: Query, **kwargs: Any) -> bool:
        model = self.get_model(kwargs.get("model", query.id))

        if not isinstance(model, TogglTag):
            return False

        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            endpoint.delete(model)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        self.notification(msg=f"Deleted tag {model.name}!")

        return True
