"""Persisted settings (PRD F9 to F11).

Two values only: the output format and the JPG quality. They are written the
moment they change, so there is no OK button, and they are read back at launch.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Signal

from .core.convert import Format

ORGANISATION = "imgIO"
APPLICATION = "imgIO"

DEFAULT_FORMAT = Format.JPG
DEFAULT_QUALITY = 90


class Settings(QObject):
    """Current format and quality, saved as soon as either changes."""

    changed = Signal()

    def __init__(self, store: QSettings | None = None) -> None:
        super().__init__()
        self._store = store or QSettings(ORGANISATION, APPLICATION)

    @property
    def format(self) -> Format:
        stored = str(self._store.value("output/format", DEFAULT_FORMAT.value))
        try:
            return Format(stored)
        except ValueError:
            return DEFAULT_FORMAT

    @format.setter
    def format(self, value: Format) -> None:
        if value is self.format:
            return
        self._store.setValue("output/format", value.value)
        self._store.sync()
        self.changed.emit()

    @property
    def quality(self) -> int:
        stored = self._store.value("output/quality", DEFAULT_QUALITY)
        try:
            return max(1, min(100, int(stored)))
        except (TypeError, ValueError):
            return DEFAULT_QUALITY

    @quality.setter
    def quality(self, value: int) -> None:
        value = max(1, min(100, int(value)))
        if value == self.quality:
            return
        self._store.setValue("output/quality", value)
        self._store.sync()
        self.changed.emit()

    def summary(self) -> str:
        """The one line under the drop zone, e.g. "Converts to JPG, quality 90"."""
        if self.format is Format.JPG:
            return f"Converts to JPG, quality {self.quality}"
        return "Converts to PNG"
