import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional

from .meta import TogglCli, TProject

log = logging.getLogger(__name__)


class TogglProjects(TogglCli):
    __slots__ = ("project_list",)

    def __init__(
        self,
        config_path: Path,
        max_results: int,
        workspace_id: Optional[int] = None,
    ) -> None:
        super().__init__(config_path, max_results, workspace_id)

        self.project_list: list[TProject] = []

    def list_projects(
        self,
        active: bool = True,
        refresh: bool = False,
        **_,
    ) -> list[TProject]:
        if not refresh and self.project_list:
            return self.project_list

        if not refresh and self.cache_path.exists():
            data = self.load_data()
            if isinstance(data, list):
                return data

        self.project_list = []

        cmd = ["ls", "-f", "+hex_color,+active"]

        run = self.base_command(cmd).splitlines()
        header_size = self.count_table(run[0])
        checked_names: set[str] = set()
        for item in run[1:]:
            item_data = self.format_line(header_size, item, checked_names)

            if item_data is None:
                continue

            name, client, active_item, project_id, hex_color = item_data

            active_item = True if active_item == "True" else False

            if not active_item and active:
                continue

            checked_names.add(name)

            tracker = TProject(
                name=name,
                project_id=int(project_id),
                client=client,
                color=hex_color,
                active=active_item,
            )
            self.project_list.append(tracker)

        self.cache_data(self.project_list)

        return self.project_list

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, "projects")
        return super().base_command(cmd)

    @staticmethod
    def project_name_formatter(name: str) -> tuple[str, int]:
        if not name:
            return "", 0
        name, project_id = name.split("(#")
        name = name.strip()
        return name, int(project_id[:-1])

    @property
    def cache_path(self) -> Path:
        return super().cache_path / Path("project_history.json")

    @property
    def CACHE_LEN(self) -> timedelta:
        return timedelta(weeks=2)
