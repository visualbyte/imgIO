# imgIO

Drag image files onto a small window and JPG or PNG copies appear beside the originals. No dialogs, no uploads, no accounts.

This is the **proof of concept** described in the PRD (`documents/PRD Drag-and-Drop Image Converter (macOS + Windows).md`). It proves the whole path works: read a file, convert it, name it without overwriting anything, and write it beside the source.

## What the proof of concept does

- Accepts dropped files and folders, plus **File → Open…** (Cmd+O).
- Reads PNG, JPEG, WebP, GIF (first frame), BMP, TIFF, and HEIC/AVIF.
- Writes one output per input, beside the source, never overwriting anything.
- Applies EXIF rotation, flattens transparency onto white for JPG, and keeps the colour profile and EXIF data.
- Converts off the main thread, one file at a time, with progress.
- Remembers format and JPG quality between launches.
- Announces a clean result with a green tick, then clears itself after three seconds. Anything skipped or failed stays on screen until the next drop.
- Reports per-file details with before/after sizes.

## What is not built yet

Settings live in a window of their own, but the update feature (F25, F26), the P1 items (app-icon drop, recursive folders), and signing and notarization are still to come. See section 10 of the PRD for the milestones.

## Requirements

- macOS 14 or later, or Windows 10 or later (only macOS is tested so far)
- Python 3.11 or later

## Run it from source

```shell
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python main.py
```

On Windows the paths are `.venv\Scripts\pip` and `.venv\Scripts\python`.

## Tests

```shell
.venv/bin/python -m pytest
.venv/bin/ruff check imgio tests main.py
```

The tests cover naming and collisions (including case and Unicode differences), format conversion, transparency, EXIF rotation, odd colour modes, animated files, unreadable files, and HEIC.

## Notes for developers

- `imgio/core/` has no Qt imports, so it can be tested and reused on its own.
- The output name is reserved by creating the file exclusively, then the image is written to a temporary file beside it and renamed into place. A crash or a full disk cannot leave a half-written image or overwrite an existing one.
- Only `PySide6-Essentials` is installed. The full `PySide6` package also pulls in Qt WebEngine, about 250 MB of code this app never uses.
- The pictograms are Lucide (ISC licence), painted from their SVG at any size and colour. See `THIRD_PARTY_NOTICES.md`.
