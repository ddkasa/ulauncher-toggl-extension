import logging as log
import sys
from pprint import pprint
from typing import Callable, Iterable, Optional, is_typeddict

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from ulauncher_toggl_extension import util
from ulauncher_toggl_extension.toggl.toggl_manager import (
    NotificationParameters,
    QueryParameters,
    TogglViewer,
)


class TogglExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

    def process_query(self, query: list[str]) -> list | Callable:
        tviewer = TogglViewer(self.preferences)

        if len(query) == 1:
            defaults = tviewer.default_options(*query)
            return self.generate_results(defaults)

        query.pop(0)

        QUERY_MATCH = {
            "stt": tviewer.start_tracker,
            "add": tviewer.add_tracker,
            "cnt": tviewer.continue_tracker,
            "stp": tviewer.stop_tracker,
            "rm": tviewer.remove_tracker,
            "sum": tviewer.total_trackers,
            "ls": tviewer.list_trackers,
        }

        method = QUERY_MATCH.get(query[0], tviewer.default_options)

        results = method(*query)
        if results is None:
            defaults = tviewer.default_options(*query)
            return self.generate_results(defaults)

        return self.generate_results(results)

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


class KeywordQueryEventListener(EventListener):
    def on_event(self, event: KeywordQueryEvent, extension: TogglExtension):
        query = event.get_query().split()
        processed_query = extension.process_query(query)

        return RenderResultListAction(processed_query)


class ItemEnterEventListener(EventListener):
    def on_event(self, event: ItemEnterEvent, extension: TogglExtension):
        data = event.get_data()

        if not data():
            return SetUserQueryAction("tgl ")

        log.info("Successfuly excecuted %s", data)

        return HideWindowAction()


if __name__ == "__main__":
    logger = log.getLogger(__name__)
    TogglExtension().run()
