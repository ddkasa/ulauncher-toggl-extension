"""Image paths for all SVG and some constant storage paths.

Examples:
    >>> from ulauncher_toggl_extension.toggl.images import CIRCULAR_SVG
    >>> new_img = CIRCULAR_SVG.format(color="#000000")
"""

# ruff: noqa: E501

import enum
from pathlib import Path
from typing import Final


class TipSeverity(enum.Enum):
    INFO = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    HINT = enum.auto()


SVG_PATH = Path("images/svg")

APP_IMG = SVG_PATH / Path("icon.svg")
START_IMG = SVG_PATH / Path("start.svg")
EDIT_IMG = SVG_PATH / Path("edit.svg")
ADD_IMG = SVG_PATH / Path("add.svg")
PROJECT_IMG = SVG_PATH / Path("project.svg")  # TODO: Needs to be created.
STOP_IMG = SVG_PATH / Path("stop.svg")
DELETE_IMG = SVG_PATH / Path("delete.svg")
CONTINUE_IMG = SVG_PATH / Path("continue.svg")
REPORT_IMG = SVG_PATH / Path("reports.svg")
BROWSER_IMG = SVG_PATH / Path("browser.svg")
BLANK_IMG = SVG_PATH / Path("blank.svg")
REFRESH_IMG = SVG_PATH / Path("refresh.svg")

TIP_IMAGES = {
    TipSeverity.HINT: SVG_PATH / Path("tip.svg"),
    TipSeverity.INFO: SVG_PATH / Path("tip.svg"),
    TipSeverity.ERROR: SVG_PATH / Path("tip-error.svg"),
    TipSeverity.WARNING: SVG_PATH / Path("tip-warning.svg"),
}

CIRCULAR_SVG: Final[str] = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" xml:space="preserve"><radialGradient id="a" cx="-24.309" cy="672.216" r="13.23" gradientTransform="matrix(0 15.3688 15.4467 0 -10127.536 629.602)" gradientUnits="userSpaceOnUse"><stop offset="0" style="stop-color:#412a4c"/><stop offset=".004" style="stop-color:#412a4c"/><stop offset="1" style="stop-color:#2c1338"/></radialGradient><rect x="52.7" y="52.7" rx="95" ry="95" width="406.6" height="406.6" fill="url(#a)"/><circle cx="256" cy="256" r="151.5" fill="{color}" stroke="transparent"/></svg>'
)

__all__ = (
    "ADD_IMG",
    "APP_IMG",
    "BLANK_IMG",
    "BROWSER_IMG",
    "CIRCULAR_SVG",
    "CONTINUE_IMG",
    "DELETE_IMG",
    "EDIT_IMG",
    "PROJECT_IMG",
    "REPORT_IMG",
    "START_IMG",
    "STOP_IMG",
    "TIP_IMAGES",
    "TipSeverity",
)
