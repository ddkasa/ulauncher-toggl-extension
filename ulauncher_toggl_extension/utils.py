# ruff: noqa: T201

from __future__ import annotations

import re
import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


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


if __name__ == "__main__":
    print(quote_text("test"))
    print(quote_text('"test"'))
