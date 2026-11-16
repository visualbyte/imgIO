"""Lucide pictograms, painted rather than shipped as image files.

Source: lucide-static 1.73.0, https://lucide.dev, ISC licence. The licence text
is in THIRD_PARTY_NOTICES at the repository root, as the licence requires.

Each icon is drawn from its SVG at any size and in any colour, so light, dark
and disabled states all get the right ink without extra assets.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget

_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"'
    ' fill="none" stroke="{colour}" stroke-width="{stroke}"'
    ' stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)

_BODIES = {
    "settings": (
        '<path d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915'
        " 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33"
        " 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0"
        ' 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34'
        ' 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915" />'
        '<circle cx="12" cy="12" r="3" />'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="10" />'
        '<path d="M12 6v6l4 2" />'
    ),
    "file-check": (
        '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588'
        ' 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z" />'
        '<path d="M14 2v5a1 1 0 0 0 1 1h5" />'
        '<path d="m9 15 2 2 4-4" />'
    ),
    "triangle-alert": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" />'
        '<path d="M12 9v4" />'
        '<path d="M12 17h.01" />'
    ),
    "file-x": (
        '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588'
        ' 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z" />'
        '<path d="M14 2v5a1 1 0 0 0 1 1h5" />'
        '<path d="m14.5 12.5-5 5" />'
        '<path d="m9.5 12.5 5 5" />'
    ),
}

#: Stroke in the 24-unit grid. Lucide's own value is 2.
DEFAULT_STROKE = 2.0

#: Status colours, as (light theme, dark theme) pairs so a thin stroke keeps
#: its contrast on either background.
STATUS_COLOURS = {
    "success": ("#1a7f37", "#4ade80"),
    "warning": ("#b45309", "#fbbf24"),
    "failure": ("#b91c1c", "#f87171"),
}

STATUS_ICONS = {
    "success": "file-check",
    "warning": "triangle-alert",
    "failure": "file-x",
}

_cache: dict[tuple[str, str, float, int], QPixmap] = {}


def is_dark(palette: QPalette) -> bool:
    return palette.color(QPalette.Window).lightness() < 128


def status_colour(kind: str, palette: QPalette) -> str:
    light, dark = STATUS_COLOURS[kind]
    return dark if is_dark(palette) else light


def pixmap(name: str, size: int, colour: str, stroke: float = DEFAULT_STROKE, dpr: float = 1.0) -> QPixmap:
    """Render one icon at `size` logical pixels, `colour`, and `stroke` grid units."""
    key = (name, colour, stroke, round(size * dpr))
    if key in _cache:
        return _cache[key]

    svg = _SVG.format(colour=colour, stroke=f"{stroke:g}", body=_BODIES[name])
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    if not renderer.isValid():
        raise ValueError(f"could not read the {name} icon")

    px = QPixmap(round(size * dpr), round(size * dpr))
    px.fill(Qt.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(dpr, dpr)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    px.setDevicePixelRatio(dpr)
    _cache[key] = px
    return px


def button_icon(name: str, size: int, colour: str, disabled_colour: str, stroke: float, dpr: float) -> QIcon:
    icon = QIcon()
    icon.addPixmap(pixmap(name, size, colour, stroke, dpr), QIcon.Normal)
    icon.addPixmap(pixmap(name, size, disabled_colour, stroke, dpr), QIcon.Disabled)
    return icon


class IconView(QWidget):
    """A fixed-size pictogram, coloured from the palette or a status colour."""

    def __init__(self, size: int = 72, parent=None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size + 8)
        self._name: str | None = None
        self._kind: str | None = None
        self.setVisible(False)

    def show_icon(self, name: str, kind: str | None = None) -> None:
        self._name = name
        self._kind = kind
        self.setVisible(True)
        self.update()

    def clear(self) -> None:
        self._name = None
        self._kind = None
        self.setVisible(False)
        self.update()

    def paintEvent(self, event):
        if not self._name:
            return

        palette = self.palette()
        if self._kind:
            colour = status_colour(self._kind, palette)
        else:
            colour = QColor(palette.color(QPalette.WindowText)).name()

        rendered = pixmap(self._name, self._size, colour, dpr=self.devicePixelRatioF())
        painter = QPainter(self)
        painter.drawPixmap(0, int((self.height() - self._size) / 2), rendered)
        painter.end()
