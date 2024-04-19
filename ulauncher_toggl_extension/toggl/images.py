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


CACHE_PATH = Path(__file__).parents[2] / "cache"

SVG_CACHE = CACHE_PATH / "svg"
SVG_CACHE.mkdir(parents=True, exist_ok=True)

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

TIP_IMAGES = {
    TipSeverity.HINT: SVG_PATH / Path("tip.svg"),
    TipSeverity.INFO: SVG_PATH / Path("tip.svg"),
    TipSeverity.ERROR: SVG_PATH / Path("tip-error.svg"),
    TipSeverity.WARNING: SVG_PATH / Path("tip-warning.svg"),
}

CIRCULAR_SVG: Final[str] = """<?xml version="1.0" encoding="utf-8"?>
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlinkwidth="512" height="512"  viewBox="0 0 512 512" enable-background="new 0 0 512 512" xml:space="preserve">
    <radialGradient id="grad" cx="256" cy="256" r="256" gradientUnits="userSpaceOnUse" width="512" height="512"  viewBox="0 0 512 512" enable-background="new 0 0 512 512" xml:space="preserve">
        <stop  offset="0" style="stop-color:#412A4C"/>
        <stop  offset="4.280270e-03" style="stop-color:#412A4C"/>
        <stop  offset="1" style="stop-color:#2C1338"/>
	</radialGradient>
    <rect x="52.7" y="52.7" rx="95" ry="95" width="406.6" height="406.6" fill="url(#grad)"/>
    <circle cx="256" cy="256" r="151.5" fill="{color}" stroke="transparent"/>
</svg>
"""

__all__ = (
    "TipSeverity",
    "APP_IMG",
    "START_IMG",
    "EDIT_IMG",
    "ADD_IMG",
    "PROJECT_IMG",
    "STOP_IMG",
    "DELETE_IMG",
    "CONTINUE_IMG",
    "REPORT_IMG",
    "BROWSER_IMG",
    "BLANK_IMG",
    "TIP_IMAGES",
    "CIRCULAR_SVG",
)
