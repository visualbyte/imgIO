"""Output naming and collision handling (PRD F4).

One rule, used by every path:

    photo.png  ->  photo.jpg
    photo.png  ->  photo (1).jpg   if photo.jpg is taken
    photo.png  ->  photo (2).jpg   if photo (1).jpg is taken too

The stem keeps the source's exact casing; the extension is always lowercase.
Existing names are compared ignoring case and Unicode normalisation, so the same
drag produces the same names on case-sensitive and case-insensitive disks.
"""

from __future__ import annotations

import os
import unicodedata
from pathlib import Path

MAX_ATTEMPTS = 10_000


def _key(name: str) -> str:
    """Comparison key: normalised for Unicode, then case-folded."""
    return unicodedata.normalize("NFC", name).casefold()


def candidate_names(stem: str, ext: str, limit: int = MAX_ATTEMPTS):
    """Yield the names to try, in order: `stem.ext`, `stem (1).ext`, ...

    `ext` includes its leading dot, so it can be joined straight onto the stem.
    """
    yield f"{stem}{ext}"
    for index in range(1, limit):
        yield f"{stem} ({index}){ext}"


def next_free_name(directory: Path, stem: str, ext: str) -> str:
    """Return the first free name in `directory` without creating it.

    Only for display and tests. Real writes go through `reserve_target`, which
    also survives two drops arriving at once.
    """
    taken = {_key(entry.name) for entry in _iter_dir(directory)}
    for name in candidate_names(stem, ext):
        if _key(name) not in taken:
            return name
    raise OSError(f"No free name for {stem}.{ext} in {directory}")


def reserve_target(source: Path, ext: str) -> Path:
    """Create and return an empty output file beside `source`.

    The file is created exclusively, so a name that already exists - even one
    that differs only by case - is never reused. The caller writes the image to
    a temporary file and then renames it over this placeholder, which keeps a
    crash or a full disk from leaving a half-written image behind.
    """
    directory = source.parent
    taken = {_key(entry.name) for entry in _iter_dir(directory)}

    for name in candidate_names(source.stem, ext):
        if _key(name) in taken:
            continue
        path = directory / name
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666))
            return path
        except FileExistsError:
            # Appeared between listing the folder and creating the file, or the
            # disk is case-insensitive and already holds a different casing.
            taken.add(_key(name))

    raise OSError(f"No free name for {source.stem}.{ext} in {directory}")


def _iter_dir(directory: Path):
    try:
        return list(os.scandir(directory))
    except OSError:
        return []
