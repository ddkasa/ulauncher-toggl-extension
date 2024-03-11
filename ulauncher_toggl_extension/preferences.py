from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ulauncher.api.client.EventListener import EventListener

if TYPE_CHECKING:
    from ulauncher.api.shared.event import (
        PreferencesEvent,
        PreferencesUpdateEvent,
    )

    from ulauncher_toggl_extension import TogglExtension

log = logging.getLogger(__name__)


class PreferencesEventListener(EventListener):
    def on_event(
        self,
        event: PreferencesEvent,
        extension: TogglExtension,
    ) -> None:
        extension.max_results = self.max_results(
            event.preferences["max_search_results"],
        )
        extension.toggl_exec_path = self.toggl_exec_path(
            event.preferences["toggl_exectuable_location"],
        )
        extension.default_project = self.default_project(
            event.preferences["project"],
        )
        extension.toggl_hints = bool(event.preferences["hints"])

    def toggl_exec_path(self, path: str) -> Path:
        loc = Path(path)
        if loc.exists():
            return loc
        log.error("TogglCli does not exist at provided Path. Using default.")
        return Path.home() / Path(".local/bin/toggl")

    def default_project(self, project: Optional[str] = None) -> int | None:
        # TODO: Need to integrate with program properly.
        log.warning("Default project is not implemented.")

        if project is not None:
            try:
                return int(project)
            except ValueError:
                pass

        log.info("Default project is not setup.")
        return None

    def max_results(self, results: Optional[str] = None) -> int:
        if results is not None:
            try:
                return int(results)
            except ValueError:
                pass
        log.info("Max search results are not setup. Using default.")
        return 10


class PreferencesUpdateEventListener(EventListener):
    def on_event(
        self,
        event: PreferencesUpdateEvent,
        extension: TogglExtension,
    ) -> None:
        new_preferences = extension.preferences.copy()
        new_preferences[event.id] = event.new_value
        extension.preferences = new_preferences
