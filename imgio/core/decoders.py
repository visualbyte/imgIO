"""Decoder plug-ins (PRD F27).

Pillow handles PNG, JPEG, WebP, GIF, BMP and TIFF out of the box. HEIC and AVIF
come from pillow-heif, which teaches Pillow to open them. Camera RAW will be
another module here later; nothing outside this file needs to change.
"""

from __future__ import annotations

from PIL import Image

# A 100 MP photo is a normal file for this app, and Pillow's default ceiling is
# about 89 MP. Raise it, and treat anything past 300 MP as a bomb rather than
# spending minutes decoding it.
Image.MAX_IMAGE_PIXELS = 300_000_000

#: File extensions offered to the user as "supported".
SUPPORTED_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".jpe", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".heif", ".avif"}
)

_heif_error: str | None = None


def register() -> None:
    """Make every optional format available to Pillow. Safe to call twice."""
    global _heif_error
    try:
        import pillow_heif
    except ImportError:
        _heif_error = "HEIC support is not installed"
        return

    pillow_heif.register_heif_opener()
    # AVIF is decoded by the same library and is useful for free.
    try:
        pillow_heif.register_avif_opener()
    except AttributeError:
        pass


def heif_unavailable_reason() -> str | None:
    """None if HEIC decoding works, otherwise a sentence for the user."""
    return _heif_error


def is_supported(path) -> bool:
    """Cheap check by extension. The real test is whether Pillow can open it."""
    return path.suffix.lower() in SUPPORTED_SUFFIXES
