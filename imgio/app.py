"""Application entry point."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtWidgets import QApplication

from . import __version__
from .core import decoders
from .settings import Settings
from .ui.main_window import MainWindow

log = logging.getLogger(__name__)


def log_directory() -> Path:
    """A per-platform place for the local support log (PRD section 8)."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Logs" / "imgIO"
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "imgIO" / "logs"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "imgIO"
    return base


def configure_logging() -> None:
    try:
        directory = log_directory()
        directory.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(directory / "imgio.log", maxBytes=512_000, backupCount=2)
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    configure_logging()
    decoders.register()
    if decoders.heif_unavailable_reason():
        log.warning("HEIC and AVIF decoding unavailable: %s", decoders.heif_unavailable_reason())

    app = QApplication(argv)
    app.setApplicationName("imgIO")
    app.setApplicationDisplayName("imgIO")
    app.setOrganizationName("imgIO")
    app.setApplicationVersion(__version__)

    window = MainWindow(Settings())
    window.show()

    # Files dropped on the app icon arrive as arguments (F18, P1).
    arguments = [Path(item) for item in argv[1:] if Path(item).exists()]
    if arguments:
        window.accept_paths(arguments)

    return app.exec()
