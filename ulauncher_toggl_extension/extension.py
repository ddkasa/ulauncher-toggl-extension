# ruff: noqa: E402
from __future__ import annotations

import contextlib
import logging
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Final, Iterable, Optional

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ActionList import ActionList
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.event import (
    ItemEnterEvent,
    KeywordQueryEvent,
    PreferencesEvent,
    PreferencesUpdateEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.utils.fuzzy_search import get_score

from ulauncher_toggl_extension.commands import (
    ActionEnum,
    AddCommand,
    ClientCommand,
    Command,
    ContinueCommand,
    CurrentTrackerCommand,
    DeleteCommand,
    EditCommand,
    HelpCommand,
    ListCommand,
    ProjectCommand,
    QueryParameters,
    RefreshCommand,
    ReportCommand,
    StartCommand,
    StopCommand,
    TagCommand,
)
from ulauncher_toggl_extension.query import Query, QueryParser

from .preferences import (
    PreferencesEventListener,
    PreferencesUpdateEventListener,
)

if TYPE_CHECKING:
    from toggl_api.reports.reports import REPORT_FORMATS
    from ulauncher.api.shared.action.BaseAction import BaseAction

log = logging.getLogger(__name__)


class TogglExtension(Extension):
    """Main extension class housing most of querying funtionality.

    Methods:
        process_query: Processes query and returns results to be displayed
            inside the launcher.
        generate_results: Converts results from TogglCli into ULauncher items.

    """

    COMMANDS: OrderedDict[str, type[Command]] = OrderedDict(
        {
            CurrentTrackerCommand.PREFIX: CurrentTrackerCommand,
            ContinueCommand.PREFIX: ContinueCommand,
            StopCommand.PREFIX: StopCommand,
            StartCommand.PREFIX: StartCommand,
            EditCommand.PREFIX: EditCommand,
            AddCommand.PREFIX: AddCommand,
            DeleteCommand.PREFIX: DeleteCommand,
            ListCommand.PREFIX: ListCommand,
            RefreshCommand.PREFIX: RefreshCommand,
            ProjectCommand.PREFIX: ProjectCommand,
            ClientCommand.PREFIX: ClientCommand,
            TagCommand.PREFIX: TagCommand,
            ReportCommand.PREFIX: ReportCommand,
            HelpCommand.PREFIX: HelpCommand,
        },
    )
    MATCH_ACTION: dict[ActionEnum, BaseAction] = {
        ActionEnum.LIST: ActionList(),
        ActionEnum.CLIPBOARD: CopyToClipboardAction,
        ActionEnum.DO_NOTHING: DoNothingAction,
        ActionEnum.HIDE: HideWindowAction,
        ActionEnum.OPEN: OpenAction,
        ActionEnum.OPEN_URL: OpenUrlAction,
        ActionEnum.RENDER_RESULT_LIST: RenderResultListAction,
        ActionEnum.RUN_SCRIPT: RunScriptAction,
        ActionEnum.SET_QUERY: SetUserQueryAction,
    }

    __slots__ = (
        "auth",
        "cache_path",
        "expiration",
        "hints",
        "max_results",
        "prefix",
        "report_format",
        "workspace_id",
    )

    def __init__(self) -> None:
        super().__init__()
        self.subscribe(
            KeywordQueryEvent,
            KeywordQueryEventListener(),
        )
        self.subscribe(
            ItemEnterEvent,
            ItemEnterEventListener(),
        )
        self.subscribe(
            PreferencesUpdateEvent,
            PreferencesUpdateEventListener(),
        )
        self.subscribe(
            PreferencesEvent,
            PreferencesEventListener(),
        )

        self.prefix = "tgl"
        self.cache_path = Path("cache")
        self.hints = True
        self.max_results = 10
        self.auth = None
        self.workspace_id = None
        self.expiration = None
        self.report_format: REPORT_FORMATS = "pdf"

    def default_results(
        self,
        query: Query,
        **kwargs,
    ) -> list[QueryParameters]:
        log.debug("Loading Default Results!")
        results: list[QueryParameters] = []
        for obj in self.COMMANDS.values():
            cmd = obj(self)
            results.extend(cmd.preview(query, **kwargs))
        return results

    def process_query(self, query: Query) -> list[ExtensionResultItem]:
        """Main method that handles querying for functionality.

        Could be refactored to be more readable as needed if more functions are
        being added.

        Args:
            query (list[str]): List of query terms to parse.

        Returns:
            query (list[str]) | Callable: List of query terms to display.
        """

        if not query.command:
            return self.generate_results(self.default_results(query))

        match = self.COMMANDS.get(query.command) or self.match_aliases(
            query.command,
        )

        if match is None:
            return self.generate_results(self.match_results(query))

        cmd = match(self)
        results = cmd.view(query)

        return self.generate_results(results)

    def match_aliases(self, query: str) -> type[Command] | None:
        # OPTIMIZE: There is probably a better way to do this.
        for cmd in self.COMMANDS.values():
            if query in cmd.ALIASES:
                return cmd

        return None

    @staticmethod
    def match_query(
        query: str,
        target: str,
        *,
        threshold: int = 40,
    ) -> bool:
        return get_score(query, target) >= threshold

    def match_results(
        self,
        query: Query,
        **kwargs,
    ) -> list[QueryParameters]:
        """Fuzzy matches query terms against a dictionary of functions using
        the `match_query` method.

        Will ignore any other parameters supplied with *_ parameters.

        Args:
            match_dict(dict): Dictionary of functions to match against.
                Will only display the first result of each viwer method.
            query (str): Query term to match against.

        Returns:
            list: List of possible matches that are produced by matched
                functions.
        """
        results: list[QueryParameters] = []
        for trg, fn in self.COMMANDS.items():
            if self.match_query(query.raw_args[0], trg):
                cmd = fn(self)
                with contextlib.suppress(IndexError):
                    results.append(cmd.preview(query, **kwargs)[0])

        return results or self.default_results(query, **kwargs)

    def create_action(
        self,
        enter: Optional[ActionEnum | Callable | str] = None,
    ) -> BaseAction:
        if isinstance(enter, ActionEnum):
            on_enter = self.MATCH_ACTION.get(enter, DoNothingAction)()
        elif enter is None:
            on_enter = DoNothingAction()
        elif isinstance(enter, str):
            on_enter = SetUserQueryAction(enter)
        else:
            on_enter = ExtensionCustomAction(enter, keep_app_open=True)

        return on_enter

    def generate_results(
        self,
        actions: Iterable[QueryParameters],
    ) -> list[ExtensionResultItem]:
        """Generates results from pre defined parameters.

        Args:
            actions: Iterable[QueryParameters]: Items to generate results from.

        Returns:
            list[ExtensionResultItem]: List of results to display in the launcher.
        """
        results = []

        i: float = 0.0
        for item in actions:
            on_enter = self.create_action(item.on_enter)
            alt_enter = self.create_action(item.on_alt_enter)

            if item.small:
                name = f"{item.name}"
                if item.description:
                    name += f": {item.description}"
                action = ExtensionSmallResultItem(
                    icon=str(item.icon),
                    name=name,
                    on_enter=on_enter,
                    on_alt_enter=alt_enter,
                    highlightable=False,
                )
            else:
                action = ExtensionResultItem(
                    icon=str(item.icon),
                    name=item.name,
                    description=item.description,
                    on_enter=on_enter,
                    on_alt_enter=alt_enter,
                    highlightable=False,
                    # REFACTOR: Add highlightable option in query params.
                )

            results.append(action)

            i += 0.5 if item.small else 1.0

            if i >= self.max_results:
                break

        return results


class KeywordQueryEventListener(EventListener):
    """Event listener for keyword query events."""

    SUBCOMMANDS: Final[frozenset[str]] = frozenset(
        (
            ProjectCommand.PREFIX,
            ClientCommand.PREFIX,
            HelpCommand.PREFIX,
            TagCommand.PREFIX,
            *ProjectCommand.ALIASES,
            *ClientCommand.ALIASES,
            *HelpCommand.ALIASES,
            *TagCommand.ALIASES,
        ),
    )

    def on_event(
        self,
        event: KeywordQueryEvent,
        extension: TogglExtension,
    ) -> None:
        raw_args = event.get_query()
        query = QueryParser(
            extension.prefix,
            extension.report_format,
            self.SUBCOMMANDS,
        ).parse(raw_args)

        processed_query = extension.process_query(query)
        return RenderResultListAction(processed_query)


class ItemEnterEventListener(EventListener):
    def on_event(  # noqa: PLR6301
        self,
        event: ItemEnterEvent,
        extension: TogglExtension,
    ) -> None:
        data = event.get_data()

        execution = data(extension=extension)
        if execution and isinstance(execution, list):
            results = extension.generate_results(execution)
            return RenderResultListAction(results)

        if not execution:
            return SetUserQueryAction("tgl ")

        log.info("Successfuly excecuted %s", data)

        return HideWindowAction()


if __name__ == "__main__":
    pass
