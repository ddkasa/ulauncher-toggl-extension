import logging as log
import sys
from pathlib import Path
from pprint import pprint
from typing import Callable, Iterable, Optional, is_typeddict

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from ulauncher_toggl_extension.toggl.toggl_manager import (
    NotificationParameters,
    QueryParameters,
    TogglViewer,
)


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

        QUERY_MATCH = {
            "start": tviewer.start_tracker,
            "stt": tviewer.start_tracker,
            "add": tviewer.add_tracker,
            "continue": tviewer.continue_tracker,
            "cnt": tviewer.continue_tracker,
            "stop": tviewer.stop_tracker,
            "stp": tviewer.stop_tracker,
            "delete": tviewer.remove_tracker,
            "remove": tviewer.remove_tracker,
            "rm": tviewer.remove_tracker,
            "report": tviewer.total_trackers,
            "sum": tviewer.total_trackers,
            "ls": tviewer.list_trackers,
            "list": tviewer.list_trackers,
        }

        method = QUERY_MATCH.get(query[0], tviewer.default_options)

        kwargs = self.parse_query(query)

        results = method(*query, **kwargs)
        if results is None:
            defaults = tviewer.default_options(*query)
            return self.generate_results(defaults)

        return self.generate_results(results)

    def parse_query(self, query: list[str]) -> dict[str, str]:
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
                    pass
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
            action = ExtensionResultItem(
                icon=str(item.icon),
                name=item.name,
                description=item.description,
                on_enter=item.on_enter,
            )
            results.append(action)

            if i == self.preferences["max_search_results"]:
                break

        return results

    @property
    def config_path(self) -> Path:
        return Path(self.preferences["toggl_config_location"])

    @property
    def default_project(self) -> int | None:
        try:
            return int(self.preferences["project"])
        except ValueError:
            log.warning("Default project not setup!")
            return None

    @property
    def max_results(self) -> int:
        return self.preferences["max_search_results"]


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
    logger = log.getLogger(__name__)
    TogglExtension().run()
