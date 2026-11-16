"""Small shared UI helpers."""

from __future__ import annotations


def human_size(size: int) -> str:
    """1_234_567 -> '1.2 MB'. Sizes are always bytes on disk."""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"
