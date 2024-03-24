"""Project fetcher and initilizer


Examples:
    >>> from ulauncher_toggl_extension.toggl.cli.project import TogglProjects
    >>> projects = TogglProjects(config_path, max_results, workspace_id)
    >>> latest_projects = projects.fetch_objects(refresh=True)
"""

from __future__ import annotations

import logging
import subprocess as sp
from datetime import timedelta
from pathlib import Path
from typing import Optional

from ulauncher_toggl_extension.toggl.dataclasses import TProject

from .meta import TogglCli

log = logging.getLogger(__name__)


class TogglProjects(TogglCli):
    """Project object that fetches and modifies objects on behalf of the
    extension.

    Attributes:
        project_list: List of projects pulled from Toggl or cache.
    """

    __slots__ = ("project_list",)

    def __init__(
        self,
        config_path: Path,
        max_results: int,
        workspace_id: Optional[int] = None,
    ) -> None:
        super().__init__(config_path, max_results, workspace_id)

        self.project_list: list[TProject] = []

    def fetch_objects(
        self,
        *,
        active: bool = True,
        refresh: bool = False,
        **_,
    ) -> list[TProject]:
        """Fetches projects from toggl and implements them in the project_list.

        Args:
            active (bool): Whether to fetch only active projects.
                Defaults to True.

        Returns:
            list[TProject]: List of projects pulled from Toggl or cache.
        """
        if not refresh and self.project_list:
            return self.project_list

        if not refresh and self.cache_path.exists():
            data = self.load_data()
            if isinstance(data, list):
                return data

        self.project_list = []

        cmd = ["ls", "-f", "+hex_color,+active"]
        try:
            run = self.base_command(cmd).splitlines()
        except sp.CalledProcessError:
            log.exception("Failed to retrieve project list.")
            return self.project_list

        header_size = self.count_table(run[0])
        checked_names: set[str] = set()
        for item in run[1:]:
            item_data = self.format_line(header_size, item, checked_names)

            if item_data is None:
                continue

            name, client, active_item, project_id, hex_color = item_data

            active_item_bool = active_item == "True"

            if not active_item and active:
                continue

            checked_names.add(name)

            tracker = TProject(
                name=name,
                project_id=int(project_id),
                client=client,
                color=hex_color,
                active=active_item_bool,
            )
            self.project_list.append(tracker)

        self.cache_data(self.project_list)

        return self.project_list

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, "projects")
        return super().base_command(cmd)

    @property
    def cache_path(self) -> Path:
        return super().cache_path / Path("project_history.json")

    @property
    def cache_len(self) -> timedelta:
        return timedelta(weeks=2)
