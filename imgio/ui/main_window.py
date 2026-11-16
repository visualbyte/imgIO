"""Main window: one stage, one background worker, no status bar (PRD F2, F15, F16)."""

from __future__ import annotations

import threading
from collections import deque
from pathlib import Path

from PySide6.QtCore import QEvent, QSize, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..core import decoders
from ..core.convert import Format, Result, Status, convert
from ..settings import Settings
from .details_window import DetailsWindow
from .human import human_size
from .icons import button_icon
from .settings_window import SettingsWindow
from .stage import Stage

#: A clean result clears itself; anything with a problem waits for the user.
CLEAN_RESULT_MS = 3000

#: The gear is 32 px with a 1.5 px stroke; 1.5 px at 32 px is 1.125 units on
#: Lucide's 24-unit grid.
GEAR_SIZE = 32
GEAR_STROKE = 1.125


def _blend(foreground: QColor, background: QColor, alpha: float) -> QColor:
    """Opaque mix of two colours, for drawing roles that need a faded ink."""
    return QColor(
        round(foreground.red() * alpha + background.red() * (1 - alpha)),
        round(foreground.green() * alpha + background.green() * (1 - alpha)),
        round(foreground.blue() * alpha + background.blue() * (1 - alpha)),
    )


class _BatchWorker(QThread):
    """Converts the queue one file at a time, off the UI thread.

    Stopping finishes the file in hand and discards the rest, so no output is
    ever left half written.
    """

    result = Signal(object)

    def __init__(self, fmt: Format, quality: int, parent=None) -> None:
        super().__init__(parent)
        self._fmt = fmt
        self._quality = quality
        self._queue: deque[Path] = deque()
        self._lock = threading.Lock()
        self._cancel = False
        self.current: Path | None = None

    def enqueue(self, paths: list[Path]) -> None:
        with self._lock:
            self._queue.extend(paths)

    def cancel(self) -> list[Path]:
        with self._lock:
            self._cancel = True
            remaining = list(self._queue)
            self._queue.clear()
        return remaining

    def run(self) -> None:
        while True:
            with self._lock:
                if self._cancel or not self._queue:
                    return
                source = self._queue.popleft()
                self.current = source
            try:
                result = convert(source, self._fmt, self._quality)
            except Exception as exc:  # noqa: BLE001 - the thread must always report back
                result = Result(source, Status.FAILED, message=str(exc) or "Something went wrong")
            self.result.emit(result)


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._worker: _BatchWorker | None = None
        self._results: list[Result] = []
        self._total = 0
        self._done = 0
        self._stopped = False
        self._cancelled_paths: list[Path] = []
        self._details_window: DetailsWindow | None = None

        self.setWindowTitle("imgIO")
        self.resize(520, 470)
        self.setMinimumSize(420, 390)

        self._stage = Stage(self)
        self._stage.pathsDropped.connect(self.accept_paths)
        self._stage.openRequested.connect(self.choose_files)
        self._stage.settingsRequested.connect(self.open_settings)
        self._stage.detailsRequested.connect(self.open_details)
        self._stage.stopRequested.connect(self.stop_batch)
        self._stage.okRequested.connect(self.dismiss_result)

        self._gear = QToolButton(self)
        self._gear.setToolTip("Settings (Cmd+,)")
        self._gear.setAutoRaise(True)
        self._gear.setFixedSize(40, 40)
        self._gear.setIconSize(QSize(GEAR_SIZE, GEAR_SIZE))
        self._gear.setStyleSheet(
            "QToolButton { border: none; border-radius: 8px; }"
            "QToolButton:hover { background: rgba(128, 128, 128, 60); }"
            "QToolButton:pressed { background: rgba(128, 128, 128, 100); }"
        )
        self._gear.clicked.connect(self.open_settings)

        # A fixed strip at the bottom: the gear belongs to the ready state, and
        # keeping it on screen (disabled elsewhere) means no state change moves
        # the stage.
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.addStretch(1)
        bottom_row.addWidget(self._gear)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)
        layout.addWidget(self._stage, 1)
        layout.addLayout(bottom_row)
        self.setCentralWidget(central)

        self._settings_window = SettingsWindow(self._settings, self)
        self._settings.changed.connect(self._sync_summary)
        self._settings_action: QAction | None = None

        self._clear_timer = QTimer(self)
        self._clear_timer.setSingleShot(True)
        self._clear_timer.timeout.connect(self.dismiss_result)

        self._build_menu()
        self._sync_summary()
        self._update_gear_icon()
        self._set_interactive(True)

        escape = QShortcut(QKeySequence("Esc"), self)
        escape.activated.connect(self._escape)

    # -- menu -------------------------------------------------------------

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        open_action = QAction("Open…", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.choose_files)
        file_menu.addAction(open_action)

        settings_action = QAction("Settings…", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.setMenuRole(QAction.PreferencesRole)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        self._settings_action = settings_action

        file_menu.addSeparator()
        quit_action = QAction("Quit imgIO", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction(f"About imgIO {__version__}", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _set_interactive(self, ready: bool) -> None:
        """The gear and its shortcut exist only while the window accepts files."""
        self._gear.setEnabled(ready)
        if self._settings_action is not None:
            self._settings_action.setEnabled(ready)

    def _update_gear_icon(self) -> None:
        palette = self.palette()
        normal = palette.color(QPalette.WindowText)
        muted = _blend(normal, palette.color(QPalette.Window), 0.35)
        self._gear.setIcon(
            button_icon(
                "settings",
                GEAR_SIZE,
                normal.name(),
                muted.name(),
                GEAR_STROKE,
                self.devicePixelRatioF(),
            )
        )

    def changeEvent(self, event):
        if event.type() == QEvent.PaletteChange:
            self._update_gear_icon()
        super().changeEvent(event)

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About imgIO",
            f"imgIO {__version__}\n\n"
            "Converts images to JPG or PNG beside the original.\n\n"
            "No account and no tracking. imgIO never sends anything about you or your "
            "images. The only network request it makes is the update check, which you "
            "can turn off.",
        )

    # -- settings ---------------------------------------------------------

    def open_settings(self) -> None:
        self._settings_window.show_and_raise()

    def _sync_summary(self) -> None:
        self._stage.set_summary(self._settings.summary())

    # -- input ------------------------------------------------------------

    def choose_files(self) -> None:
        pattern = " ".join(f"*{suffix}" for suffix in sorted(decoders.SUPPORTED_SUFFIXES))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose images to convert",
            "",
            f"Images ({pattern});;All files (*)",
        )
        if files:
            self.accept_paths([Path(name) for name in files])

    @Slot(list)
    def accept_paths(self, paths: list[Path]) -> None:
        files = self._expand(paths)
        if not files:
            self._clear_timer.stop()
            self._stage.show_result(
                "warning",
                "Nothing to convert",
                "No supported images in that drop.",
                ok=True,
            )
            self._set_interactive(False)
            return

        if self._worker is not None:
            # A drop during a batch joins the queue.
            self._worker.enqueue(files)
            self._total += len(files)
            self._show_progress()
            return

        self._start_batch(files)

    def _expand(self, paths: list[Path]) -> list[Path]:
        """Folders contribute their supported images, not subfolders (F14)."""
        files: list[Path] = []
        for path in paths:
            if path.is_dir():
                try:
                    entries = sorted(path.iterdir())
                except OSError:
                    continue
                files.extend(
                    entry
                    for entry in entries
                    if entry.is_file() and not entry.name.startswith(".") and decoders.is_supported(entry)
                )
            elif path.is_file():
                files.append(path)
        return files

    # -- batch ------------------------------------------------------------

    def _start_batch(self, files: list[Path]) -> None:
        self._clear_timer.stop()
        self._close_details()
        self._results.clear()
        self._cancelled_paths.clear()
        self._done = 0
        self._stopped = False
        self._total = len(files)

        worker = _BatchWorker(self._settings.format, self._settings.quality, self)
        worker.result.connect(self._on_result)
        worker.finished.connect(self._on_finished)
        self._worker = worker
        worker.enqueue(files)
        worker.start()
        self._show_progress()

    def _show_progress(self) -> None:
        if self._worker is None:
            return
        current = min(self._done + 1, self._total)
        remaining = self._total - self._done
        name = self._worker.current.name if self._worker.current else ""
        self._stage.show_progress(current, self._total, name, stoppable=remaining > 1 and not self._stopped)
        self._set_interactive(False)

    @Slot(object)
    def _on_result(self, result: Result) -> None:
        self._results.append(result)
        self._done += 1
        if self._worker is not None and self._done < self._total:
            self._show_progress()

    @Slot()
    def _on_finished(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()

        for path in self._cancelled_paths:
            self._results.append(Result(path, Status.CANCELLED, message="Stopped"))
        self._cancelled_paths.clear()

        self._show_result()

    def stop_batch(self) -> None:
        if self._worker is None or self._stopped:
            return
        self._stopped = True
        self._cancelled_paths = self._worker.cancel()
        self._stage.show_stopping()
        self._set_interactive(False)

    # -- results ----------------------------------------------------------

    def _show_result(self) -> None:
        counts = {status: 0 for status in Status}
        for result in self._results:
            counts[result.status] += 1

        converted = counts[Status.CONVERTED]
        skipped = counts[Status.SKIPPED]
        failed = counts[Status.FAILED]
        cancelled = counts[Status.CANCELLED]
        problems = skipped + failed + cancelled

        if cancelled:
            processed = converted + skipped + failed
            self._stage.show_result(
                "warning",
                f"Stopped after {processed} of {self._total}",
                f"{cancelled} not converted",
                details=True,
                ok=True,
            )
            self._set_interactive(False)
            return

        if not problems:
            self._stage.show_result("success", self._headline(converted), self._size_line())
            self._set_interactive(False)
            self._clear_timer.start(CLEAN_RESULT_MS)
            return

        kind = "failure" if failed and converted == 0 else "warning"
        if converted == 0:
            headline = "Nothing converted"
        else:
            headline = self._headline(converted)
            if skipped:
                headline += f", {skipped} skipped"
            if failed:
                headline += f", {failed} failed"

        self._stage.show_result(
            kind,
            headline,
            self._problem_line(),
            details=len(self._results) > 1,
            ok=True,
        )
        self._set_interactive(False)

    def _headline(self, converted: int) -> str:
        return "1 converted" if converted == 1 else f"{converted} converted"

    def _size_line(self) -> str:
        saved = sum(result.saved_bytes for result in self._results if result.status is Status.CONVERTED)
        if saved > 0:
            return f"{human_size(saved)} smaller"
        # A larger output is kept by design (PRD F8); exact sizes are in Details.
        return "Saved beside the originals"

    def _problem_line(self) -> str:
        problems = [result for result in self._results if result.status is not Status.CONVERTED]
        if len(problems) == 1:
            problem = problems[0]
            return f"{problem.source.name} — {problem.message.lower()}"
        if problems:
            return "Open Details for the reasons"
        return ""

    def _summary_text(self) -> str:
        counts = {status: 0 for status in Status}
        for result in self._results:
            counts[result.status] += 1
        parts = []
        for status, word in (
            (Status.CONVERTED, "converted"),
            (Status.SKIPPED, "skipped"),
            (Status.FAILED, "failed"),
            (Status.CANCELLED, "not converted"),
        ):
            if counts[status]:
                parts.append(f"{counts[status]} {word}")
        return ", ".join(parts) or "No files"

    # -- dismissal --------------------------------------------------------

    def dismiss_result(self) -> None:
        self._clear_timer.stop()
        self._stage.show_ready()
        self._set_interactive(True)

    def _escape(self) -> None:
        if self._details_window is not None and self._details_window.isVisible():
            self._details_window.close()
        elif self._stage.ok_visible():
            self.dismiss_result()

    def open_details(self) -> None:
        if self._details_window is not None:
            self._details_window.raise_()
            self._details_window.activateWindow()
            return
        window = DetailsWindow(list(self._results), self._summary_text(), self)
        window.finished.connect(self._details_closed)
        self._details_window = window
        window.show()
        window.raise_()

    def _details_closed(self, _result: int) -> None:
        self._details_window = None

    def _close_details(self) -> None:
        if self._details_window is not None:
            self._details_window.close()
            self._details_window = None

    # -- shutdown ---------------------------------------------------------

    def closeEvent(self, event):
        self._clear_timer.stop()
        self._close_details()
        if self._worker is not None:
            self._worker.cancel()
            if not self._worker.wait(10000):
                self._worker.terminate()
                self._worker.wait(1000)
        super().closeEvent(event)
