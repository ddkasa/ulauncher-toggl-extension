import logging as log
import sys
from pprint import pprint
from typing import Callable, Iterable, Optional, is_typeddict

from gi.repository import Notify
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from ulauncher_toggl_extension import util
from ulauncher_toggl_extension.toggl.toggl_manager import (
    NotificationParameters,
    QueryParameters,
    TogglManager,
)


class TogglExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.notification = None

    def process_query(self, query: list[str]) -> list | Callable:
        tracker_obj = TogglManager(self.preferences)

        if len(query) == 1:
            defaults = tracker_obj.default_options(*query)
            return self.generate_results(defaults)

        query.pop(0)

        QUERY_MATCH = {
            "stt": tracker_obj.start_tracker,
            "add": tracker_obj.add_tracker,
            "cnt": tracker_obj.continue_tracker,
            "stp": tracker_obj.stop_tracker,
            "rm": tracker_obj.remove_tracker,
            "sum": tracker_obj.summate_trackers,
            "ls": tracker_obj.list_trackers,
        }

        method = QUERY_MATCH.get(query[0], tracker_obj.default_options)

        results = method(*query)
        if results is None:
            defaults = tracker_obj.default_options(*query)
            return self.generate_results(defaults)
        elif isinstance(results, NotificationParameters):
            self.show_notification(results)
            return HideWindowAction

        return self.generate_results(results)

    def show_notification(
        self, data: NotificationParameters, on_close: Optional[Callable] = None
    ):
        icon = str(data.icon.absolute())
        if not Notify.is_initted():
            Notify.init("TogglExtension")
        # icon = util.get_icon_path()
        if self.notification is None:
            self.notification = Notify.Notification.new(data.title, data.body, icon)
        else:
            self.notification.update(data.title, data.body, icon)
        if on_close is not None:
            self.notification.connect("closed", on_close)
        self.notification.show()

    def generate_results(
        self, actions: Iterable[QueryParameters]
    ) -> list[ExtensionResultItem]:
        results = []
        for item in actions:
            action = ExtensionResultItem(
                icon=str(item.icon),
                name=item.name,
                description=item.description,
                on_enter=item.on_enter,
            )
            results.append(action)

        return results


class KeywordQueryEventListener(EventListener):
    def on_event(self, event: KeywordQueryEvent, extension: TogglExtension):
        query = event.get_query().split()
        processed_query = extension.process_query(query)

        return RenderResultListAction(processed_query)


class ItemEnterEventListener(EventListener):
    def on_event(self, event: ItemEnterEvent, extension: TogglExtension):
        # event is instance of ItemEnterEvent
        log.debug("Item Enter Event")
        data = event.get_data()

        log.debug(data)
        # do additional actions here...

        # you may want to return another list of results
        return HideWindowAction(keep_app_open=False)


if __name__ == "__main__":
    logger = log.getLogger(__name__)
    TogglExtension().run()
