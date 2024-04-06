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

import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from gi.repository import Notify


def ensure_import(package):
    try:
        return __import__(package)
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", "--user", package])  # noqa: S603
    return __import__(package)


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
