import enum
from pathlib import Path


class TipSeverity(enum.Enum):
    INFO = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()


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
    TipSeverity.INFO: SVG_PATH / Path("tip.svg"),
    TipSeverity.ERROR: SVG_PATH / Path("tip-error.svg"),
    TipSeverity.WARNING: SVG_PATH / Path("tip-warning.svg"),
}

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
)
