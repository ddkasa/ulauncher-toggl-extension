from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any, Literal, Optional

from httpx import HTTPStatusError
from toggl_api import ClientBody, ClientEndpoint, TogglClient, TogglQuery

from ulauncher_toggl_extension.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    DELETE_IMG,
    EDIT_IMG,
    REFRESH_IMG,
)

from .meta import QueryParameters, SubCommand

if TYPE_CHECKING:
    from ulauncher_toggl_extension.query import Query

log = logging.getLogger(__name__)


class ClientCommand(SubCommand):
    """Subcommand for all client based tasks."""

    PREFIX = "client"
    ALIASES = ("cli",)
    ICON = APP_IMG  # TODO: Need a custom image
    EXPIRATION = None
    OPTIONS = ()

    def get_models(self, query: Query, **kwargs: Any) -> list[TogglClient]:
        del kwargs
        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            clients = endpoint.collect(refresh=query.refresh)
        except HTTPStatusError as err:
            self.handle_error(err)
            clients = endpoint.collect()

        clients.sort(key=lambda x: x.timestamp, reverse=query.sort_order)
        return clients

    def get_model(
        self,
        client_id: Optional[int | TogglClient | str] = None,
        *,
        refresh: bool = False,
    ) -> TogglClient | None:
        if client_id is None or isinstance(client_id, TogglClient):
            return client_id

        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)
        if isinstance(client_id, str):
            client = list(endpoint.query(TogglQuery("name", client_id)))
            if client:
                return client[0]
            return None

        try:
            client = endpoint.get(client_id, refresh=refresh)
        except HTTPStatusError as err:
            self.handle_error(err)
            return None

        return client  # type: ignore[return-value]


class ListClientCommand(ClientCommand):
    """List all clients."""

    PREFIX = "list"
    ALIASES = ("l", "ls")
    ICON = BROWSER_IMG
    OPTIONS = ("refresh", ":", "^-")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
                self.get_cmd() + " refresh",
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        if query.id:
            kwargs["model"] = self.get_model(query.id, refresh=query.refresh)
            if kwargs["model"]:
                return self.handle(query, **kwargs)  # type: ignore[return-value]

        self.amend_query(query.raw_args)
        data: list[partial] = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    client,
                    self.get_cmd() + f" :{client.id}",
                    fmt_str="{name}",
                )
                for client in self.get_models(query, **kwargs)
            ]

        return self._paginator(query, data, page=kwargs.get("page", 0))


class AddClientCommand(ClientCommand):
    """Create a new client."""

    PREFIX = "add"
    ALIASES = ("a", "add", "create", "insert")
    ICON = ADD_IMG
    OPTIONS = ("refresh", '"', "^-")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        self.amend_query(query.raw_args)
        return [
            QueryParameters(
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

    def view(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        self.amend_query(query.raw_args)
        data: list[QueryParameters] = kwargs.get("data", [])
        if not data:
            for client in self.get_models(query, **kwargs):
                mdl = self.process_model(
                    client,
                    self.generate_query(client),
                )
                data.append(mdl[0])

        return self._paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def generate_query(self, model: TogglClient) -> str:
        query = self.get_cmd()
        if model.name:
            query += ' "{model.name}"'
        return query

    def handle(self, query: Query, **_: Any) -> bool:
        if not isinstance(query.name, str):
            return False

        body = ClientBody(query.name)
        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)

        try:
            client = endpoint.add(body)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        if not client:
            return False

        self.notification(msg=f"Created client {body.name}!")
        return True


class DeleteClientCommand(ClientCommand):
    """Delete a client."""

    PREFIX = "delete"
    ALIASES = ("d", "del", "rm", "remove")
    ICON = DELETE_IMG
    ESSENTIAL = True
    OPTIONS = ("refresh", ":", "^-")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        self.amend_query(query.raw_args)
        data: list[partial] = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    client,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=client,
                        **kwargs,
                    ),
                )
                for client in self.get_models(query, **kwargs)
            ]

        return self._paginator(query, data, page=kwargs.get("page", 0))

    def handle(self, query: Query, **kwargs: Any) -> bool:
        model = kwargs.get("model", query.id)

        if isinstance(model, str):
            model = self.get_model(model)

        if model is None:
            return False

        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)

        try:
            endpoint.delete(model)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        self.notification(msg=f"Deleted client {model}!")
        return True


class EditClientCommand(ClientCommand):
    """Edit a client."""

    PREFIX = "edit"
    ALIASES = ("e", "change", "amend")
    ICON = EDIT_IMG
    ESSENTIAL = True
    OPTIONS = ("refresh", '"', ":", "^-")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query.raw_args)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        self.amend_query(query.raw_args)
        data: list[partial] = kwargs.get("data", [])
        if not data:
            data = [
                partial(
                    self.process_model,
                    client,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=client,
                        **kwargs,
                    ),
                )
                for client in self.get_models(query, **kwargs)
            ]

        return self._paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def handle(self, query: Query, **kwargs: Any) -> bool:
        model = kwargs.get("model", query.id)

        if not isinstance(model, TogglClient | int):
            model = self.get_model(model)

        if model is None:
            return False

        body = ClientBody(query.name)
        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)

        try:
            client = endpoint.edit(model, body)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        if not client:
            return False

        self.notification(msg=f"Edited client {body.name}!")

        return True


class RefreshClientCommand(ClientCommand):
    """Refresh specific clients."""

    PREFIX = "refresh"
    ALIASES = ("re", "update")
    ICON = REFRESH_IMG
    ESSENTIAL = True

    OPTIONS = ("refresh", "distinct", ":")

    def preview(self, query: Query, **kwargs: Any) -> list[QueryParameters]:  # noqa: PLR6301
        del query, kwargs
        return []

    def view(self, query: Query, **kwargs: Any) -> list[QueryParameters]:
        data: list[partial] = kwargs.get("data", [])
        if not data:
            query.distinct = not query.distinct
            data = [
                partial(
                    self.process_model,
                    client,
                    partial(
                        self.call_pickle,
                        method="handle",
                        query=query,
                        model=client,
                        **kwargs,
                    ),
                    fmt_str="{name}",
                )
                for client in self.get_models(query, **kwargs)
            ]

        return self._paginator(query, data, page=kwargs.get("page", 0))

    def handle(self, query: Query, **kwargs: Any) -> Literal[False]:
        model = kwargs.get("model", query.id)
        if isinstance(model, str):
            model = self.get_model(model)

        if model is None:
            return False

        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            model = endpoint.get(model, refresh=True)
        except HTTPStatusError as err:
            self.handle_error(err)
            return False

        if model is None:
            return False

        self.notification(f"Successfully refreshed client '{model.name}'!")

        return False
