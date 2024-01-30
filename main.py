import logging
from pathlib import Path
from typing import Callable, Iterable

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem

from ulauncher_toggl_extension.toggl.toggl_cli import TogglCli
from ulauncher_toggl_extension.toggl.toggl_manager import QueryParameters, TogglViewer

log = logging.getLogger(__name__)


class TogglExtension(Extension):
    __slots__ = "latest_trackers"

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

        self.latest_trackers = []

    def process_query(self, query: list[str]) -> list | Callable:
        tviewer = TogglViewer(self)

        if not self.latest_trackers:
            self.latest_trackers = tviewer.tcli.list_trackers()

        if len(query) == 1:
            defaults = tviewer.default_options(*query)
            return self.generate_results(defaults)

        query.pop(0)

        # TODO: Switch this to a fuzzy finder.

        QUERY_MATCH = {
            "start": tviewer.start_tracker,
            "stt": tviewer.start_tracker,
            "add": tviewer.add_tracker,
            "continue": tviewer.continue_tracker,
            "cnt": tviewer.continue_tracker,
            "stop": tviewer.stop_tracker,
            "stp": tviewer.stop_tracker,
            "edit": tviewer.edit_tracker,
            "now": tviewer.edit_tracker,
            "delete": tviewer.remove_tracker,
            "remove": tviewer.remove_tracker,
            "rm": tviewer.remove_tracker,
            "report": tviewer.total_trackers,
            "sum": tviewer.total_trackers,
            "ls": tviewer.list_trackers,
            "list": tviewer.list_trackers,
            "project": tviewer.get_projects,
            "projects": tviewer.get_projects,
        }

        method = QUERY_MATCH.get(query[0], tviewer.default_options)

        query.pop(0)
        kwargs = self.parse_query(query)

        results = method(*query, **kwargs)
        if results is None:
            defaults = tviewer.default_options(*query)
            return self.generate_results(defaults)

        return self.generate_results(results)

    def parse_query(self, query: list[str]) -> dict[str, str]:
        # TODO: Input sanitizing in order to throw away invalid arguments.
        arguments = {}
        for i, item in enumerate(query):
            if i == 0:
                arguments["action"] = item
            elif item[0] == "#":
                arguments["tags"] = item[1:]
            elif item[0] == "@":
                item = item[1:]
                try:
                    item = int(item)
                except ValueError:
                    log.error("Failed to parse project: %s", item)
                    continue
                arguments["project"] = item
            elif item[0] == ">":
                arguments["start"] = item[1:]
            elif item[0] == "<":
                arguments["stop"] = item[1:]

        return arguments

    def generate_results(
        self, actions: Iterable[QueryParameters]
    ) -> list[ExtensionResultItem]:
        results = []
        for i, item in enumerate(actions, start=1):
            if item.small:
                action = ExtensionSmallResultItem(
                    icon=str(item.icon),
                    name=f"{item.name}: {item.description}",
                    description=item.description,
                    on_enter=item.on_enter,
                    on_alt_enter=item.on_alt_enter,
                    highlightable=False,
                )
            else:
                action = ExtensionResultItem(
                    icon=str(item.icon),
                    name=item.name,
                    description=item.description,
                    on_enter=item.on_enter,
                    on_alt_enter=item.on_alt_enter,
                )
            results.append(action)

            if i == self.preferences["max_search_results"]:
                break

        return results

    @property
    def toggl_exec_path(self) -> Path:
        loc = Path(self.preferences["toggl_exectuable_location"])
        if loc.exists():
            return loc
        log.error("Toggl does not exist. Using default.")
        return Path.home() / Path(".local/bin/toggl")

    @property
    def default_project(self) -> int | None:
        try:
            return int(self.preferences["project"])
        except ValueError:
            log.debug("Default project not setup!")
            return

    @property
    def max_results(self) -> int:
        try:
            return int(self.preferences["max_search_results"])
        except ValueError:
            return 10

    @property
    def toggled_hints(self) -> bool:
        return self.preferences["hints"]


class KeywordQueryEventListener(EventListener):
    def on_event(self, event: KeywordQueryEvent, extension: TogglExtension):
        query = event.get_query().split()
        processed_query = extension.process_query(query)

        return RenderResultListAction(processed_query)


class ItemEnterEventListener(EventListener):
    def on_event(self, event: ItemEnterEvent, extension: TogglExtension):
        data = event.get_data()
        execution = data()
        if not isinstance(execution, bool):
            log.debug("Display a lot more options")
            results = extension.generate_results(execution)
            return RenderResultListAction(results)
        if not execution:
            return SetUserQueryAction("tgl ")

        log.info("Successfuly excecuted %s", data)

        return HideWindowAction()


if __name__ == "__main__":
    TogglExtension().run()
