from __future__ import annotations

import logging
from functools import partial
from typing import Optional

from httpx import HTTPStatusError
from toggl_api import ClientBody, ClientEndpoint, TogglClient

from ulauncher_toggl_extension.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    DELETE_IMG,
    EDIT_IMG,
)

from .meta import QueryParameters, SubCommand

log = logging.getLogger(__name__)


class ClientCommand(SubCommand):
    """Subcommand for all client based tasks."""

    PREFIX = "client"
    ALIASES = ("c", "cli")
    ICON = APP_IMG  # TODO: Need a custom image
    EXPIRATION = None

    def get_models(self, **kwargs) -> list[TogglClient]:
        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            clients = endpoint.collect(refresh=kwargs.get("refresh", False))
        except HTTPStatusError as err:
            log.exception("%s")
            self.notification(str(err))
            return []

        clients.sort(key=lambda x: x.timestamp, reverse=True)
        return clients

    def get_client(
        self,
        client_id: Optional[int] = None,
        *,
        refresh: bool = False,
    ) -> TogglClient | None:
        if client_id is None:
            return None
        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)
        try:
            client = endpoint.get(client_id, refresh=refresh)
        except HTTPStatusError as err:
            log.exception("%s")
            self.notification(str(err))
            return None

        return client


class ListClientCommand(ClientCommand):
    """List all clients."""

    PREFIX = "list"
    ALIASES = ("l", "ls")
    ICON = BROWSER_IMG

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
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
                for client in self.get_models(**kwargs)
            ]

        return self.paginator(query, data, page=kwargs.get("page", 0))


class AddClientCommand(ClientCommand):
    """Create a new client."""

    PREFIX = "add"
    ALIASES = ("a", "add", "create", "insert")
    ICON = ADD_IMG

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
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

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
        data: list[QueryParameters] = kwargs.get("data", [])
        if not data:
            for client in self.get_models(**kwargs):
                mdl = self.process_model(
                    client,
                    self.generate_query(client),
                )
                data.append(mdl[0])

        return self.paginator(
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

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        name = kwargs.get("description")

        if not isinstance(name, str):
            return False

        body = ClientBody(name, kwargs.get("status"), kwargs.get("notes"))
        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)

        try:
            client = endpoint.add(body)
        except HTTPStatusError as err:
            log.exception("%s")
            self.notification(str(err))
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

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
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
                for client in self.get_models(**kwargs)
            ]

        return self.paginator(query, data, page=kwargs.get("page", 0))

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        model = kwargs.get("model") or kwargs.get("name")

        if not isinstance(model, TogglClient | int):
            return False

        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)

        try:
            endpoint.delete(model)
        except HTTPStatusError as err:
            log.exception("%s")
            self.notification(str(err))
            return False

        self.notification(msg=f"Deleted client {model}!")
        return True


class EditClientCommand(ClientCommand):
    """Edit a client."""

    PREFIX = "edit"
    ALIASES = ("e", "change", "amend")
    ICON = EDIT_IMG
    ESSENTIAL = True

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        self.amend_query(query)
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
                for client in self.get_models(**kwargs)
            ]

        return self.paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        name = kwargs.get("description")
        model = kwargs.get("model") or name

        if not isinstance(model, TogglClient | int):
            return False

        body = ClientBody(
            name if isinstance(name, str) else None,
            kwargs.get("status"),
            kwargs.get("notes"),
        )
        endpoint = ClientEndpoint(self.workspace_id, self.auth, self.cache)

        try:
            client = endpoint.edit(model, body)
        except HTTPStatusError as err:
            log.exception("%s")
            self.notification(str(err))
            return False

        if not client:
            return False

        self.notification(msg=f"Edited client {body.name}!")

        return True
