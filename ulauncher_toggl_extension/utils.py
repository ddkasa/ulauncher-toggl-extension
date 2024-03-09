import subprocess
import sys
from pathlib import Path


def ensure_import(package):
    try:
        return __import__(package)
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", "--user", package])
    return __import__(package)


def sanitize_path(path: str | Path) -> str:
    path = str(path).replace(" ", "-")
    return path
