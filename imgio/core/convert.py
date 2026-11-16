"""The conversion itself (PRD F3 to F8, F12, F13, F17).

`convert()` takes one source path and the current settings and writes exactly
one output beside the source. It has no Qt imports, so it can be tested on its
own and reused by any future interface.

Every supported input is converted, including one that is already in the target
format: the product is a converter, and the settings decide the output.
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from . import decoders
from .naming import reserve_target

log = logging.getLogger(__name__)


class Format(str, Enum):
    JPG = "JPG"
    PNG = "PNG"

    @property
    def extension(self) -> str:
        return ".jpg" if self is Format.JPG else ".png"

    @property
    def pillow_name(self) -> str:
        return "JPEG" if self is Format.JPG else "PNG"


class Status(str, Enum):
    CONVERTED = "converted"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "not converted"


@dataclass
class Result:
    source: Path
    status: Status
    output: Path | None = None
    message: str = ""
    source_bytes: int = 0
    output_bytes: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def saved_bytes(self) -> int:
        return self.source_bytes - self.output_bytes


def convert(source: Path, fmt: Format, quality: int = 90) -> Result:
    """Convert one file. Never raises for a bad file, and never touches it."""
    source = Path(source)
    try:
        source_bytes = source.stat().st_size
    except OSError as exc:
        return Result(source, Status.FAILED, message=f"Can't read this file ({exc.strerror})")

    try:
        with Image.open(source) as opened:
            return _convert_image(opened, source, fmt, quality, source_bytes)
    except UnidentifiedImageError:
        if decoders.is_supported(source):
            return Result(source, Status.FAILED, message="File could not be read", source_bytes=source_bytes)
        return Result(source, Status.SKIPPED, message="Not a supported image", source_bytes=source_bytes)
    except Image.DecompressionBombError:
        return Result(source, Status.FAILED, message="Image is too large to convert", source_bytes=source_bytes)
    except PermissionError:
        return Result(source, Status.FAILED, message="Can't read this file", source_bytes=source_bytes)
    except OSError as exc:
        return Result(source, Status.FAILED, message=_os_message("File could not be read", exc), source_bytes=source_bytes)
    except Exception:
        log.exception("Unexpected failure converting %s", source)
        return Result(source, Status.FAILED, message="Something went wrong reading this file", source_bytes=source_bytes)


def _convert_image(opened: Image.Image, source: Path, fmt: Format, quality: int, source_bytes: int) -> Result:
    notes: list[str] = []

    if getattr(opened, "n_frames", 1) > 1:
        notes.append("First frame only")
        opened.seek(0)

    image = ImageOps.exif_transpose(opened)

    save_options: dict = {}
    icc_profile = image.info.get("icc_profile")
    if icc_profile:
        save_options["icc_profile"] = icc_profile

    if fmt is Format.JPG:
        image = _flatten_to_rgb(image)
        quality = max(1, min(100, int(quality)))
        save_options["quality"] = quality
        exif = image.info.get("exif") or opened.info.get("exif")
        if exif:
            save_options["exif"] = exif
    else:
        image = _fit_png_mode(image)

    target: Path | None = None
    temporary: Path | None = None
    try:
        target = reserve_target(source, fmt.extension)
        handle, temporary_name = tempfile.mkstemp(dir=target.parent, prefix=".imgio-", suffix=".tmp")
        os.close(handle)
        temporary = Path(temporary_name)
        image.save(temporary, format=fmt.pillow_name, **save_options)
        os.replace(temporary, target)
    except PermissionError:
        _discard(temporary, target)
        return Result(source, Status.FAILED, message="Can't write to this folder", source_bytes=source_bytes)
    except OSError as exc:
        _discard(temporary, target)
        return Result(source, Status.FAILED, message=_os_message("Could not save the file", exc), source_bytes=source_bytes)
    except Exception:
        _discard(temporary, target)
        log.exception("Unexpected failure saving %s", source)
        return Result(source, Status.FAILED, message="Something went wrong saving this file", source_bytes=source_bytes)
    finally:
        image.close()

    try:
        output_bytes = target.stat().st_size
    except OSError:
        output_bytes = 0

    return Result(
        source,
        Status.CONVERTED,
        output=target,
        source_bytes=source_bytes,
        output_bytes=output_bytes,
        notes=notes,
    )


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    """JPG has no transparency, so put transparent pixels on white (F12)."""
    if image.mode in ("I;16", "I;16B", "I;16L", "I", "F"):
        image = image.convert("I").point(lambda value: value / 256).convert("L")
    if image.mode == "P":
        image = image.convert("RGBA" if "transparency" in image.info else "RGB")
    if image.mode in ("RGBA", "LA", "PA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        rgba.close()
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def _fit_png_mode(image: Image.Image) -> Image.Image:
    """PNG keeps transparency, but is saved as an 8-bit mode."""
    if image.mode in ("I;16", "I;16B", "I;16L", "I", "F"):
        image = image.convert("I").point(lambda value: value / 256).convert("L")
    if image.mode in ("RGB", "RGBA", "L", "LA", "P"):
        return image
    return image.convert("RGBA" if "transparency" in image.info else "RGB")


def _os_message(prefix: str, exc: OSError) -> str:
    """'File could not be read (No such file)' but never '(None)'."""
    reason = exc.strerror or ""
    return f"{prefix} ({reason})" if reason else prefix


def _discard(temporary: Path | None, placeholder: Path | None) -> None:
    """Leave nothing behind if the write failed."""
    for path in (temporary, placeholder):
        if path is None:
            continue
        try:
            path.unlink()
        except OSError:
            pass
