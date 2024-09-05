from __future__ import annotations

import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from httpx import BasicAuth
from toggl_api import JSONCache, UserEndpoint
from toggl_api.config import AuthenticationError, generate_authentication, use_togglrc
from ulauncher.api.client.EventListener import EventListener

from ulauncher_toggl_extension.date_time import parse_timedelta
from ulauncher_toggl_extension.images import TIP_IMAGES, TipSeverity
from ulauncher_toggl_extension.utils import show_notification

if TYPE_CHECKING:
    from ulauncher.api.shared.event import (
        PreferencesEvent,
        PreferencesUpdateEvent,
    )

    from ulauncher_toggl_extension import TogglExtension

log = logging.getLogger(__name__)


class PreferencesEventListener(EventListener):
    """Event listener for preferences.

    Will validate and provide defaults if incorrect or missing values are
    provided.

    Methods:
        authentication: Generates and verifies authentication credentials.
        on_event: Updates extension preferences and checks for changes.
        workspace_id: Sets up the workspace id.
        max_results: Checks if max search results are set.
        expiration: Parses custom expiration date for trackers.
    """

    def on_event(
        self,
        event: PreferencesEvent,
        extension: TogglExtension,
    ) -> None:
        extension.prefix = event.preferences.get("toggl_keyword", "tgl")
        extension.cache_path = event.preferences["cache"] or Path.home() / (
            ".cache/ulauncher_toggl_extension"
        )
        extension.max_results = self.max_results(
            event.preferences["max_search_results"],
        )
        wid = self.workspace(
            os.environ.get("TOGGL_WORKSPACE_ID") or event.preferences["workspace"],
        )
        extension.workspace_id = wid
        extension.hints = event.preferences["hints"] == "true"
        extension.auth = self.authentication(
            wid,
            extension.cache_path,
            event.preferences["api_token"],
        )
        extension.expiration = self.parse_expiration(event.preferences["expiration"])

    @staticmethod
    def authentication(
        workspace: int,
        cache: Path,
        api_key: Optional[str] = None,
    ) -> BasicAuth:
        """Method checking for authentication and verifying its validity.

        Checks preferences -> environment variables -> .togglrc file.

        Raises:
            AuthenticationError: If authentication fails or is missing.

        Returns:
            BasicAuth: BasicAuth object that is used with httpx client.
        """
        if api_key:
            auth = BasicAuth(api_key, "api_token")
        else:
            try:
                auth = generate_authentication()
            except AuthenticationError:
                try:
                    auth = use_togglrc()
                except AuthenticationError:
                    log.exception("Authentication is missing.")
                    raise

        endpoint = UserEndpoint(
            workspace_id=workspace,
            auth=auth,
            cache=JSONCache(cache, timedelta(0)),
        )
        if not endpoint.check_authentication():
            err = (
                "Authentication failed with provided details."
                "Check your config or the Toggl API might be down."
            )
            show_notification(err, TIP_IMAGES[TipSeverity.ERROR])
            raise AuthenticationError(err)

        return auth

    @staticmethod
    def workspace(workspace_id: Optional[str] = None) -> int:
        if workspace_id is not None:
            try:
                return int(workspace_id)
            except ValueError:
                log.exception("Workspace ID is not an integer. %s")

        err = "Workspace ID is not setup correctly!"
        show_notification(err, TIP_IMAGES[TipSeverity.ERROR])
        raise ValueError(err)

    @staticmethod
    def max_results(results: Optional[str] = None) -> int:
        if results is not None:
            try:
                return int(results)
            except ValueError:
                pass
        log.info("Max search results are not setup. Using default.")
        return 10

    @staticmethod
    def parse_expiration(expiration: str) -> timedelta | None:
        if not expiration:
            return None
        try:
            td = parse_timedelta(expiration)
            log.info(
                "User set tracker cache expiration at %s seconds.",
                int(td.total_seconds()),
            )
            return td  # noqa: TRY300
        except ValueError:
            msg = "Invalid expiration time set: %s."
            show_notification(msg % expiration, TIP_IMAGES[TipSeverity.ERROR])
            log.exception(msg, expiration)
            return None


class PreferencesUpdateEventListener(EventListener):
    def on_event(  # noqa: PLR6301
        self,
        event: PreferencesUpdateEvent,
        extension: TogglExtension,
    ) -> None:
        new_preferences = extension.preferences.copy()
        new_preferences[event.id] = event.new_value
        extension.preferences = new_preferences
