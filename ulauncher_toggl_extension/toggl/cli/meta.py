from __future__ import annotations

import json
import logging
import os
import re
import subprocess as sp
from abc import ABCMeta, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Optional

from ulauncher_toggl_extension.toggl.images import CACHE_PATH
from ulauncher_toggl_extension.toggl.serializers import (
    CustomDeserializer,
    CustomSerializer,
)

if TYPE_CHECKING:
    from pathlib import Path

log = logging.getLogger(__name__)


class TogglCli(metaclass=ABCMeta):
    __slots__ = (
        "toggl_exec_path",
        "max_results",
        "workspace_id",
        "_cache_path",
    )

    def __init__(
        self,
        config_path: Path,
        max_results: int,
        workspace_id: Optional[int] = None,
    ) -> None:
        self.toggl_exec_path = str(config_path)
        self.max_results = max_results
        self.workspace_id = workspace_id

        self._cache_path = CACHE_PATH / "json"
        self._cache_path.mkdir(parents=True, exist_ok=True)

    def base_command(self, cmd: list[str]) -> str:
        cmd.insert(0, self.toggl_exec_path)
        tcmd = " ".join(cmd)
        log.debug("Running subcommand: %s", tcmd)

        try:
            run = sp.run(
                tcmd,
                text=True,
                shell=True,  # noqa: S602
                env=dict(os.environ),
                capture_output=True,
                check=False,
            )
        except sp.CalledProcessError:
            log.exception("'%s failed to run.'", tcmd)
            raise

        return str(run.stdout.strip())

    def count_table(self, header: str) -> list[int]:
        right_aligned = {"start", "stop", "duration"}

        count = []
        current_word = ""

        for index, letter in enumerate(header):
            right = current_word.strip().lower() in right_aligned

            if (
                not right
                and current_word
                and current_word[-1] == " "
                and letter != " "
                and any(x.isalpha() for x in current_word)
            ) or (right and current_word[-1] != " " and letter == " "):
                current_word = ""
                count.append(index + 1)

            current_word += letter

        return count

    def format_line(
        self,
        header_size: list[int],
        item: str,
        duplicate_names: Optional[set] = None,
    ) -> list[str] | None:
        prev = 0
        item_data = []
        for index in header_size:
            d = item[prev:index].strip()
            if isinstance(duplicate_names, set) and d in duplicate_names:
                return None
            item_data.append(d)
            prev = index
        item_data.append(item[prev:].strip())
        return item_data

    def format_id_str(self, text: str) -> tuple[str, int]:
        name, item_id = text.split("(")

        item_id = re.sub(r"[\)\(#]", "", item_id)
        name = name.strip()

        return name, int(item_id)

    def cache_data(self, data: list) -> None:
        log.debug("Caching new data to %s", self.cache_path)
        data = data.copy()
        data.insert(0, datetime.now(tz=UTC))
        with self.cache_path.open("w", encoding="utf-8") as file:
            file.write(json.dumps(data, cls=CustomSerializer))

    def load_data(self) -> list | None:
        log.debug("Loading cached data from %s", self.cache_path)
        with self.cache_path.open("r", encoding="utf-8") as file:
            data = json.loads(file.read(), cls=CustomDeserializer)

        date = data.pop(0)
        if datetime.now(tz=UTC) - self.cache_len >= date:
            log.info(
                "%s: Cache out of date. Will request new data.",
                self.__str__,
            )
            return None

        return data

    @property
    @abstractmethod
    def cache_path(self) -> Path:
        return self._cache_path

    @property
    @abstractmethod
    def cache_len(self) -> timedelta:
        return timedelta()

    def quote_text(self, text: str) -> str:
        return '"' + text.strip('"') + '"'
