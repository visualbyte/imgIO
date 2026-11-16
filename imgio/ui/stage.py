"""The stage: the one area of the window, with three looks.

1. Ready     - a dashed box inviting a drop, with the current setting.
2. Progress  - no box: clock icon, "Converting 3 of 12", file name, bar, Stop.
3. Result    - no box: an icon, a headline, one line of detail, and buttons.

Progress and Result share two fixed slots, an icon slot and an action slot, so
moving from one to the other moves nothing on screen. The dashed outline is a
drop instruction, so it is painted only in Ready, and while a file is dragged
over the window in any state.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QPainter,
    QPalette,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .icons import STATUS_ICONS, IconView

TITLE_STYLE = "font-size: 17px; font-weight: 600; background: transparent;"

ICON_SLOT_HEIGHT = 80
ACTION_SLOT_HEIGHT = 48


class ClickableLabel(QLabel):
    clicked = Signal()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class ThinBar(QWidget):
    """A slim progress bar, painted from the palette."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(280, 6)
        self._fraction = 0.0

    def set_fraction(self, value: float) -> None:
        value = max(0.0, min(1.0, value))
        if value != self._fraction:
            self._fraction = value
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        palette = self.palette()

        track = QColor(palette.color(QPalette.WindowText))
        track.setAlpha(40)
        painter.setPen(Qt.NoPen)
        painter.setBrush(track)
        painter.drawRoundedRect(self.rect(), 3, 3)

        if self._fraction > 0:
            fill = QRectF(0, 0, self.width() * self._fraction, self.height())
            painter.setBrush(palette.color(QPalette.Highlight))
            painter.drawRoundedRect(fill, 3, 3)
        painter.end()


class Stage(QFrame):
    """The whole content area. One look per state, nothing else on screen."""

    pathsDropped = Signal(list)
    openRequested = Signal()
    settingsRequested = Signal()
    detailsRequested = Signal()
    stopRequested = Signal()
    okRequested = Signal()

    MODE_READY = "ready"
    MODE_PROGRESS = "progress"
    MODE_RESULT = "result"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(320, 200)

        self._mode = self.MODE_READY
        self._highlight = False

        self._icon = IconView(72, self)
        self._icon.setFixedHeight(ICON_SLOT_HEIGHT)

        self._title = QLabel("Drop images here", self)
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setWordWrap(True)

        self._subtitle = QLabel("or click to choose files", self)
        self._subtitle.setAlignment(Qt.AlignCenter)
        self._subtitle.setWordWrap(True)

        self._settings_line = ClickableLabel(self)
        self._settings_line.setAlignment(Qt.AlignCenter)
        self._settings_line.setCursor(Qt.PointingHandCursor)
        self._settings_line.setToolTip("Open Settings")
        self._settings_line.clicked.connect(self.settingsRequested)

        self._bar = ThinBar(self)
        bar_holder = QWidget(self)
        bar_holder.setFixedHeight(6)
        bar_layout = QHBoxLayout(bar_holder)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.addStretch(1)
        bar_layout.addWidget(self._bar)
        bar_layout.addStretch(1)

        self._stop_button = QPushButton("Stop", self)
        self._stop_button.setToolTip("Stops after the current file")
        self._stop_button.clicked.connect(self._on_stop)

        self._details_button = QPushButton("Details", self)
        self._details_button.clicked.connect(self._on_details)

        self._ok_button = QPushButton("OK", self)
        self._ok_button.setDefault(True)
        self._ok_button.clicked.connect(self._on_ok)

        buttons_holder = QWidget(self)
        buttons_holder.setFixedHeight(34)
        buttons = QHBoxLayout(buttons_holder)
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)
        buttons.addStretch(1)
        buttons.addWidget(self._stop_button)
        buttons.addWidget(self._details_button)
        buttons.addWidget(self._ok_button)
        buttons.addStretch(1)

        # Fixed height, so the block never changes size between states.
        self._action = QWidget(self)
        self._action.setFixedHeight(ACTION_SLOT_HEIGHT)
        action_layout = QVBoxLayout(self._action)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        action_layout.addWidget(bar_holder)
        action_layout.addWidget(buttons_holder)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)
        layout.addStretch(1)
        layout.addWidget(self._icon, 0, Qt.AlignHCenter)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._settings_line)
        layout.addWidget(self._action)
        layout.addStretch(1)

        self.show_ready()

    # -- states -----------------------------------------------------------

    def show_ready(self) -> None:
        self._mode = self.MODE_READY
        self._icon.clear()
        self._title.setText("Drop images here")
        self._set_subtitle("or click to choose files", muted=True)
        self._settings_line.setVisible(True)
        self._action.setVisible(False)
        self._reset_buttons()
        self.update()

    def show_progress(self, current: int, total: int, filename: str, stoppable: bool) -> None:
        self._mode = self.MODE_PROGRESS
        self._icon.show_icon("clock")

        if total > 1:
            self._title.setText(f"Converting {current} of {total}")
            self._bar.setVisible(True)
            self._bar.set_fraction((current - 1) / total)
        else:
            self._title.setText("Converting…")
            self._bar.setVisible(False)

        elided = QFontMetrics(self._subtitle.font()).elidedText(filename, Qt.ElideMiddle, 300)
        self._set_subtitle(elided, muted=True)
        self._settings_line.setVisible(False)
        self._action.setVisible(True)
        self._reset_buttons()
        self._stop_button.setVisible(stoppable)
        self.update()

    def show_stopping(self) -> None:
        self._mode = self.MODE_PROGRESS
        self._icon.show_icon("clock")
        self._title.setText("Stopping…")
        self._set_subtitle("Finishing the current file", muted=True)
        self._bar.setVisible(False)
        self._settings_line.setVisible(False)
        self._action.setVisible(True)
        self._reset_buttons()
        self.update()

    def show_result(
        self,
        kind: str,
        headline: str,
        detail: str = "",
        *,
        details: bool = False,
        ok: bool = False,
    ) -> None:
        """kind is "success", "warning" or "failure"."""
        self._mode = self.MODE_RESULT
        self._icon.show_icon(STATUS_ICONS[kind], kind)
        self._title.setText(headline)
        self._set_subtitle(detail, muted=False)
        self._bar.setVisible(False)
        self._settings_line.setVisible(False)
        self._action.setVisible(True)
        self._reset_buttons()
        self._details_button.setVisible(details)
        self._ok_button.setVisible(ok)
        self.update()

    def set_summary(self, text: str) -> None:
        self._settings_line.setText(f'<a href="#" style="color: palette(text);">{text}</a>')

    def ok_visible(self) -> bool:
        return self._ok_button.isVisible()

    # -- helpers ----------------------------------------------------------

    def _set_subtitle(self, text: str, *, muted: bool) -> None:
        self._subtitle.setText(text)
        self._subtitle.setVisible(bool(text))
        self._subtitle.setForegroundRole(
            QPalette.PlaceholderText if muted else QPalette.WindowText
        )

    def _reset_buttons(self) -> None:
        for button in (self._stop_button, self._details_button, self._ok_button):
            button.setVisible(False)
            button.setEnabled(True)

    def _on_stop(self) -> None:
        # Lock before acting, so a second click cannot arrive.
        self._stop_button.setEnabled(False)
        self.stopRequested.emit()

    def _on_details(self) -> None:
        self._details_button.setEnabled(False)
        self.detailsRequested.emit()
        QTimer.singleShot(0, lambda: self._details_button.setEnabled(True))

    def _on_ok(self) -> None:
        self._ok_button.setEnabled(False)
        self.okRequested.emit()

    # -- input ------------------------------------------------------------

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._mode == self.MODE_READY:
            self.openRequested.emit()
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if self._local_paths(event):
            event.acceptProposedAction()
            self._set_highlight(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_highlight(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_highlight(False)
        paths = self._local_paths(event)
        if not paths:
            event.ignore()
            return
        event.acceptProposedAction()
        self.pathsDropped.emit(paths)

    @staticmethod
    def _local_paths(event) -> list[Path]:
        mime = event.mimeData()
        if not mime.hasUrls():
            return []
        return [Path(url.toLocalFile()) for url in mime.urls() if url.isLocalFile()]

    def _set_highlight(self, on: bool) -> None:
        if on != self._highlight:
            self._highlight = on
            self.update()

    # -- painting ---------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        palette = self.palette()

        if self._mode == self.MODE_READY or self._highlight:
            if self._highlight:
                pen = QPen(palette.color(QPalette.Highlight), 2, Qt.SolidLine)
                background = QColor(palette.color(QPalette.Highlight))
                background.setAlpha(28)
                painter.setBrush(QBrush(background))
            else:
                border = QColor(palette.color(QPalette.WindowText))
                border.setAlpha(90)
                pen = QPen(border, 2, Qt.DashLine)
                painter.setBrush(QBrush(palette.color(QPalette.Base)))

            painter.setPen(pen)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)

        painter.end()
