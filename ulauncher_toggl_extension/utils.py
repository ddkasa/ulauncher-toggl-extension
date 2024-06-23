"""Utility module with a bunch of functions used throughout the extension.

Functions:
    ensure_import: Installs the package if its missing and imports it.
    quote_text: Small function to surround text with double quotes.
    show_notification: Hooks into the system framework to display a notification.

Examples:
    >>> from ulauncher_toggl_extension.utils import show_notification
    >>> show_notification("test", "test.png")
"""


# ruff: noqa: T201

from __future__ import annotations

import importlib
import logging
import re
import subprocess  # noqa: S404
import sys
from pathlib import Path
from typing import Callable, Optional

from gi.repository import Notify

log = logging.getLogger(__name__)


def ensure_import(package, package_name):
    try:
        return importlib.import_module(package)
    except ModuleNotFoundError:
        log.info("Package %s is missing. Installing...", package_name)
        subprocess.call(
            [  # noqa: S603
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--user",
                package_name,
            ],
        )
    return importlib.import_module(package)


def sanitize_path(path: str | Path) -> str:
    return str(path).replace(" ", "-")


def quote_text(text: str) -> str:
    text = re.sub(r'"', "", text)
    return '"' + text.strip() + '"'


def show_notification(
    msg: str,
    img: Path,
    title: str = "Toggl Extension",
    on_close: Optional[Callable] = None,
) -> None:
    icon = str(Path(__file__).parents[1] / img)
    if not Notify.is_initted():
        Notify.init("TogglExtension")
    notification = Notify.Notification.new(title, msg, icon)
    if on_close is not None:
        notification.connect("closed", on_close)
    notification.show()


if __name__ == "__main__":
    print(quote_text("test"))
    print(quote_text('"test"'))
