from __future__ import annotations

from functools import partial

from toggl_api import TagEndpoint, TogglTag

from ulauncher_toggl_extension.images import (
    ADD_IMG,
    APP_IMG,
    BROWSER_IMG,
    DELETE_IMG,
    EDIT_IMG,
)

from .meta import QueryParameters, SubCommand


class TagCommand(SubCommand):
    """Subcommand for all tag based tasks."""

    PREFIX = "tag"
    ALIASES = ("t", "tags")
    ICON = APP_IMG  # TODO: Need a custom image
    EXPIRATION = None

    def get_models(self, **kwargs) -> list[TogglTag]:
        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)
        tags = endpoint.collect(refresh=kwargs.get("refresh", False))
        tags.sort(key=lambda x: x.timestamp, reverse=True)
        return tags


class ListTagCommand(TagCommand):
    """List all tags."""

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
        data: list[QueryParameters] = kwargs.get("data", [])
        if not data:
            for project in self.get_models(**kwargs):
                mdl = self.process_model(
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
                data.append(mdl[0])

        return self.paginator(query, data, page=kwargs.get("page", 0))


class AddTagCommand(TagCommand):
    """Create a new tag."""

    PREFIX = "add"
    ALIASES = ("a", "add", "create")
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
        data: list[partial] = kwargs.get("data", [])

        if not data:
            data = [
                partial(
                    self.process_model,
                    tag,
                    self.generate_query(tag),
                )
                for tag in self.get_models(**kwargs)
            ]

        return self.paginator(
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

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        name = kwargs.get("description")
        if not isinstance(name, str):
            return False

        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)
        endpoint.add(name)

        self.notification(msg=f"Created a new tag: {name}!")
        return True


class EditTagCommand(TagCommand):
    """Edit an existing tag."""

    PREFIX = "edit"
    ALIASES = ("e", "amend")
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
                for tag in self.get_models(**kwargs)
            ]

        return self.paginator(
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

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        model = kwargs.get("model")
        name = kwargs.get("description")
        if not isinstance(model, TogglTag) or not isinstance(name, str):
            return False
        old_name = model.name
        model.name = name

        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)

        endpoint.edit(model)

        self.notification(f"Updated tag {old_name} with a new name {name}!")

        return True


class DeleteTagCommand(TagCommand):
    """Delete an existing tag."""

    PREFIX = "delete"
    ALIASES = ("d", "rm", "remove", "del")
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
                for tag in self.get_models(**kwargs)
            ]

        return self.paginator(
            query,
            data,
            static=self.preview(query, **kwargs),
            page=kwargs.get("page", 0),
        )

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        model = kwargs.get("model")
        if not isinstance(model, TogglTag):
            return False

        endpoint = TagEndpoint(self.workspace_id, self.auth, self.cache)
        endpoint.delete(model)

        self.notification(msg=f"Deleted tag {model.name}!")

        return True
