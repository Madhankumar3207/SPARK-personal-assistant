"""Application and persistent-runtime paths for source and PyInstaller runs."""

import os
import sys
from pathlib import Path


def application_dir():
    """Return the project directory, or the directory containing SPARK.exe."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def runtime_file(*parts):
    """Return a persistent app-data file path and ensure its parent exists."""
    if getattr(sys, "frozen", False):
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "SPARK"
    else:
        root = application_dir()
    path = root.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
