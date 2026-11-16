"""Settings window (PRD F9 to F11, F24)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..core.convert import Format
from ..settings import Settings

QUALITY_HINT = "Lower quality means smaller files and more visible compression."
PNG_NOTE = "PNG is lossless, so there is no quality setting."


class SettingsWindow(QDialog):
    """Non-modal, saves on every change, no OK or Cancel."""

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("imgIO Settings")
        self.setModal(False)
        self.setMinimumWidth(320)

        self._settings = settings

        # -- output format ------------------------------------------------
        self._jpg = QRadioButton("JPG")
        self._png = QRadioButton("PNG")
        group = QButtonGroup(self)
        group.addButton(self._jpg)
        group.addButton(self._png)
        format_row = QHBoxLayout()
        format_row.addWidget(self._jpg)
        format_row.addWidget(self._png)
        format_row.addStretch(1)

        # -- quality ------------------------------------------------------
        self._quality = QSlider(Qt.Horizontal)
        self._quality.setRange(1, 100)
        self._quality.setSingleStep(1)
        self._quality.setPageStep(5)
        self._number = QSpinBox()
        self._number.setRange(1, 100)
        self._number.setFixedWidth(64)
        quality_row = QHBoxLayout()
        quality_row.addWidget(self._quality, 1)
        quality_row.addWidget(self._number)

        hint = QLabel(QUALITY_HINT)
        hint.setWordWrap(True)
        hint.setForegroundRole(QPalette.PlaceholderText)

        # The quality block and the PNG note never appear together: one of them
        # always applies, so no dead control is shown.
        self._quality_block = QWidget(self)
        quality_layout = QVBoxLayout(self._quality_block)
        quality_layout.setContentsMargins(0, 0, 0, 0)
        quality_layout.setSpacing(6)
        quality_layout.addWidget(QLabel("JPG quality"))
        quality_layout.addLayout(quality_row)
        quality_layout.addWidget(hint)

        self._png_note = QLabel(PNG_NOTE)
        self._png_note.setWordWrap(True)
        self._png_note.setForegroundRole(QPalette.PlaceholderText)

        output_box = QGroupBox("Output")
        output_layout = QVBoxLayout(output_box)
        output_layout.addWidget(QLabel("Format"))
        output_layout.addLayout(format_row)
        output_layout.addSpacing(6)
        output_layout.addWidget(self._quality_block)
        output_layout.addWidget(self._png_note)

        # -- footer -------------------------------------------------------
        about = QLabel(f"imgIO {__version__} · No account. No tracking.")
        about.setForegroundRole(QPalette.PlaceholderText)
        close_button = QPushButton("Done")
        close_button.setDefault(True)
        close_button.clicked.connect(self.close)
        footer = QHBoxLayout()
        footer.addWidget(about)
        footer.addStretch(1)
        footer.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(output_box)
        layout.addStretch(1)
        layout.addLayout(footer)

        # -- wiring -------------------------------------------------------
        self._quality.valueChanged.connect(self._number.setValue)
        self._number.valueChanged.connect(self._quality.setValue)
        self._quality.valueChanged.connect(self._on_quality_changed)
        self._jpg.toggled.connect(self._on_format_changed)

        # Measure the taller JPG layout once, so switching format never changes
        # the window height; the slack goes below the group, not inside it.
        self._png_note.setVisible(False)
        self.setMinimumHeight(self.sizeHint().height())

        self._load()

    def _load(self) -> None:
        current = self._settings.format
        self._jpg.setChecked(current is Format.JPG)
        self._png.setChecked(current is Format.PNG)
        self._quality.setValue(self._settings.quality)
        self._number.setValue(self._settings.quality)
        self._refresh_quality()

    def _on_format_changed(self, _checked: bool) -> None:
        self._settings.format = Format.JPG if self._jpg.isChecked() else Format.PNG
        self._refresh_quality()

    def _on_quality_changed(self, value: int) -> None:
        self._settings.quality = value

    def _refresh_quality(self) -> None:
        is_jpg = self._settings.format is Format.JPG
        self._quality_block.setVisible(is_jpg)
        self._png_note.setVisible(not is_jpg)

    def show_and_raise(self) -> None:
        self._load()
        self.show()
        self.raise_()
        self.activateWindow()
