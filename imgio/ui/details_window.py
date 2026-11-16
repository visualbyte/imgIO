"""The per-file report: a window of its own (PRD F32).

Fifty failed files belong here, not in the main window, which only ever shows a
headline. One row per file, with what happened and the sizes.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..core.convert import Result, Status
from .human import human_size


def outcome_text(result: Result) -> str:
    if result.status is Status.CONVERTED:
        return "Converted"
    if result.status is Status.SKIPPED:
        return f"Skipped — {result.message.lower()}"
    if result.status is Status.CANCELLED:
        return "Not converted — stopped"
    return f"Failed — {result.message.lower()}"


def size_text(result: Result) -> str:
    if result.status is Status.CONVERTED:
        return f"{human_size(result.source_bytes)} → {human_size(result.output_bytes)}"
    return "—"


class DetailsWindow(QDialog):
    """Non-modal report window. One instance at a time, rebuilt per batch."""

    def __init__(self, results: list[Result], summary: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("imgIO — Details")
        self.setModal(False)
        self.resize(680, 420)
        self.setMinimumSize(520, 300)

        self._results = results

        heading = QLabel(summary, self)
        heading.setStyleSheet("font-size: 15px; font-weight: 600;")
        hint = QLabel("Double-click a converted file to show it in Finder.", self)
        hint.setForegroundRole(QPalette.PlaceholderText)

        self._table = QTableWidget(len(results), 4, self)
        self._table.setHorizontalHeaderLabels(["File", "Result", "Output", "Size"])
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setWordWrap(False)
        self._table.setShowGrid(False)
        self._table.itemDoubleClicked.connect(self._reveal)
        self._table.itemSelectionChanged.connect(self._update_actions)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        for column in range(4):
            self._table.horizontalHeaderItem(column).setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._fill()

        self._reveal_button = QPushButton("Show in Finder", self)
        self._reveal_button.setEnabled(False)
        self._reveal_button.clicked.connect(self._reveal_selected)
        close_button = QPushButton("Close", self)
        close_button.setDefault(True)
        close_button.clicked.connect(self.close)

        buttons = QHBoxLayout()
        buttons.addWidget(self._reveal_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        layout.addWidget(heading)
        layout.addWidget(hint)
        layout.addWidget(self._table, 1)
        layout.addLayout(buttons)

        self._style_table()

    def _fill(self) -> None:
        for row, result in enumerate(self._results):
            output = result.output.name if result.output else "—"
            cells = (
                result.source.name,
                outcome_text(result),
                output,
                size_text(result),
            )
            for column, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, str(result.output or result.source))
                if result.status is not Status.CONVERTED:
                    item.setForeground(QColor(self.palette().color(QPalette.PlaceholderText)))
                self._table.setItem(row, column, item)

    def _style_table(self) -> None:
        palette = self.palette()
        base = palette.color(QPalette.Base).name()
        text = palette.color(QPalette.Text).name()
        border = QColor(palette.color(QPalette.WindowText))
        border.setAlpha(45)
        self._table.setStyleSheet(
            f"QTableWidget {{ background: {base}; color: {text};"
            f" border: 1px solid {border.name(QColor.HexArgb)}; border-radius: 6px; }}"
            "QTableWidget::item { padding: 4px 6px; }"
            f"QTableWidget::item:selected {{ background: {palette.color(QPalette.Highlight).name()};"
            f" color: {palette.color(QPalette.HighlightedText).name()}; }}"
            f"QHeaderView::section {{ background: {base}; color: {text}; border: none;"
            f" border-bottom: 1px solid rgba(128, 128, 128, 60); padding: 4px 6px; }}"
        )

    def _update_actions(self) -> None:
        row = self._table.currentRow()
        converted = 0 <= row < len(self._results) and self._results[row].status is Status.CONVERTED
        self._reveal_button.setEnabled(converted)

    def _reveal_selected(self) -> None:
        row = self._table.currentRow()
        if 0 <= row < len(self._results):
            self._reveal(self._table.item(row, 0))

    def _reveal(self, item: QTableWidgetItem) -> None:
        path = Path(item.data(Qt.UserRole))
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", "-R", str(path)], check=False)
            elif sys.platform.startswith("win"):
                subprocess.run(["explorer", "/select,", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path.parent)], check=False)
        except OSError:
            pass
