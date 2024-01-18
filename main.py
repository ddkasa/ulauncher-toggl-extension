import logging
import sys
from pprint import pprint

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from ulauncher_toggl_extension.toggl.toggl_manager import TogglManager, TogglTracker


class TogglExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

    def parse_query(self, query: list[str]) -> list:
        tracker_obj = TogglManager(self.preferences)

        if len(query) == 1:
            return self.generate_results({})

        query.pop(0)

        QUERY_MATCH = {
            "stt": tracker_obj.start_tracker,
            "add": tracker_obj.add_tracker,
            "cnt": tracker_obj.continue_tracker,
            "stp": tracker_obj.stop_tracker,
            "rm": tracker_obj.remove_tracker,
            "sum": tracker_obj.summate_trackers,
            "gl": tracker_obj.summate_trackers,
            "ls": tracker_obj.list_trackers,
        }

        method = QUERY_MATCH.get(query[0], tracker_obj.default_options)

        results = method(query)

        return self.generate_results(results)

    def generate_results(self, settings: dict) -> list:
        items = []
        for i in range(5):
            items.append(
                ExtensionResultItem(
                    icon="images/icon.svg",
                    name="Item %s" % i,
                    description="Item description %s" % i,
                    on_enter=HideWindowAction(),
                )
            )
        return items


class KeywordQueryEventListener(EventListener):
    def on_event(self, event: KeywordQueryEvent, extension: TogglExtension):
        query = event.get_query().split()
        processed_query = extension.parse_query(query)

        return RenderResultListAction(processed_query)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    TogglExtension().run()
