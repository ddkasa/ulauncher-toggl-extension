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
import subprocess  # noqa: S404
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

import gi

gi.require_version("Notify", "0.7")

from gi.repository import Notify  # noqa: E402

if TYPE_CHECKING:
    from types import ModuleType

log = logging.getLogger(__name__)


def quote_member(text: str, member: str) -> str:
    text, member = str(text), str(member)
    if member.lower() in text.lower():
        return f'"{text}"'
    return member


def _ensure_import(package: str, version: Optional[str] = None) -> ModuleType:
    module = importlib.import_module(package)
    if version is not None and module.__version__ != version:
        raise ModuleNotFoundError
    return module


def ensure_import(
    package: str,
    package_name: Optional[str] = None,
    version: Optional[str] = None,
) -> ModuleType:
    """Utility for installing external dependencies.

    Args:
        package: Name of the package to important. Same as you would declare in
            a `import package` statement.
        package_name: Backup name for installing the package if not present as
            PyPi package names may differ.
        version: Optional version to look for when installing a missing
            package.

    Raises:
        ModuleNotFoundError: If package is not found at all.

    Return:
        Module: The correct module for use in the application.
    """
    package_name = package_name or package
    try:
        return _ensure_import(package, version)
    except ModuleNotFoundError:
        log.info("Package %s is missing. Installing...", package_name)
        subprocess.call(  # noqa: S603
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                f"{package_name}=={version}" if version else package_name,
            ],
        )
        return importlib.import_module(package)


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
    pass
