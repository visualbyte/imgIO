# PRD: imgIO — Drag-and-Drop Image Converter (macOS + Windows)

Nov 16, 2026 · @Vishal Gupta

**Revision 11, 16 Nov 2026.** The PNG mode no longer shows a disabled quality control; the row is replaced by one sentence. The interface stops saying "no telemetry" and uses plain wording instead. Revision 10 brought in Lucide pictograms and fixed icon and action slots. Revision 9 made every button lock on the click. Revision 8 moved the gear to a fixed bottom strip and disabled it outside the ready state. Revision 7 made the session area one stage with three states, removed the status bar, and added Stop (F31) and a separate Details window (F32). Revision 6 enlarged the window and introduced the green tick. Revision 5 recorded the proof of concept and fixed PyInstaller as the packaging tool. Revision 4 fixed the toolkit at PySide6 6.12 and the minimum macOS at 14. Revision 3 made conversion unconditional (F21 to F23 withdrawn, F8 replaced them). Revision 2 settled the name, output-naming rules, owner identity and packaging constraints. See "Decided" in section 10.

## 1. Overview

A small desktop converter for macOS and Windows: the user drags image files onto its window, and JPG or PNG copies appear in the same folder as the originals, with no further clicks. Every dropped image is written at the format and quality currently selected, including files that are already in that format.

**Problem.** Converting a few images (a WebP download to PNG, a screenshot to a smaller JPG) currently means opening an editor or uploading files to a web converter. This tool reduces that to one drag.

**Name:** imgIO. **Owner and developer:** Vishal Gupta. **Platforms:** macOS (Apple Silicon and Intel) and Windows (x64 and ARM64), one codebase, native-feeling UI. **Distribution:** open-source public release through the owner's own channels (direct download) in v1. macOS signing and notarization, and licence compliance, are release requirements. Windows ships unsigned in v1 by the owner's decision.

## 2. Goals, non-goals and success metrics

v1 does one thing: drop images, get JPG or PNG files beside the originals, fast and without ever damaging the user's files.

**Goals**

1. Conversion starts the moment files are dropped. No confirm button, no dialog.
2. Two output formats (JPG, PNG) and a JPG quality setting, all kept in a separate Settings window and remembered between launches.
3. One codebase with a UI that feels native on both macOS and Windows.
4. Originals are never modified, and existing files are never overwritten.

**Non-goals for v1**

- Resizing, cropping, editing, renaming or metadata editing
- Output formats other than JPG and PNG (WebP, HEIC and AVIF output are future work)
- Linux, mobile, command-line mode, cloud upload, camera RAW input in v1 (planned later, so the design must allow it)

**Success targets** (proposed; adjust after the first prototype)

| Metric | Target |
| --- | --- |
| Drop to files written, one 12 MP JPEG | under 1 s on a mid-range laptop |
| App cold start | under 2 s |
| Installed size | under 150 MB per platform |
| Data-loss bugs (overwrite, corrupt output, modified source) | 0 in the test plan |

## 3. Users and core use cases

The user is anyone who occasionally needs a different image format and wants it without opening an editor: designers, photographers, office and marketing staff. No technical knowledge is assumed.

1. **Shrink screenshots.** Drag 10 PNG screenshots in, get 10 smaller JPGs beside them.
2. **Fix a download.** Drag a WebP picture in, get a PNG that any tool accepts.
3. **Share phone photos.** Drag HEIC photos in, get JPGs (required in v1).
4. **Re-encode in place of a better setting.** Drag JPGs in while JPG/60 is selected and each one comes back as a new JPG at 60 beside the original, for a smaller working copy.
5. **Change the setting once.** Open Settings, switch to PNG or lower the JPG quality, and the next drop uses it.

## 4. Functional requirements

P0 = must ship in v1, P1 = should ship in v1, P2 = later.

| ID | Requirement | Priority |
| --- | --- | --- |
| F1 | The main window accepts dropped files (and folders, see F14). | P0 |
| F2 | Conversion starts immediately on drop, with no confirmation step. | P0 |
| F3 | Each output is written to the same directory as its source, with the same base name and the new extension (`photo.png` becomes `photo.jpg`). Files dropped from different folders each output beside their own source. | P0 |
| F4 | Never overwrite. Target is `<stem>.<ext>`, where the stem keeps the source's exact casing and the extension is always lowercase. If the target exists, use `<stem> (1).<ext>`, then `<stem> (2).<ext>`, incrementing until a free name is found; exactly one space before the `(`. Existing names are compared case-insensitively and Unicode-normalised, so `Photo.jpg` blocks `photo.jpg` on every filesystem, and the suffix keeps the source's casing (`Photo.png` gives `Photo (1).jpg`). | P0 |
| F5 | Source files are never modified, moved or deleted. | P0 |
| F6 | Input formats: PNG, JPEG, WebP, GIF (first frame only), BMP, TIFF. Detect the format from file contents, not the extension. | P0 |
| F7 | HEIC/HEIF input (and AVIF if the library supports it) via a decoder plug-in, since iPhone photos are a main use case. | P0 |
| F8 | Every supported input produces exactly one output at the current format and quality. A file already in the output format is re-encoded like any other: no prompt, no skip path, no separate naming. | P0 |
| F9 | Setting: output format, JPG or PNG, in the Settings window. Default JPG. | P0 |
| F10 | Setting: JPG quality, 1 to 100. Default 90. Disabled when PNG is selected. | P0 |
| F11 | Settings persist between launches, save the moment they change (no OK button), and apply from the next drop. | P0 |
| F12 | Transparent pixels are flattened onto white when saving as JPG. | P0 |
| F13 | Respect EXIF orientation: the output is upright, and no orientation tag is left that would rotate it twice. | P0 |
| F14 | A dropped folder converts the supported images directly inside it (not subfolders). Recursive conversion is P2. | P1 |
| F15 | Convert on a background thread. The UI stays responsive and shows progress for multi-file drops. | P0 |
| F16 | After a drop, show the result in the stage: an icon, a headline and one line of detail. A clean result clears itself after three seconds; anything else waits for OK or a new drop. No message appears below the stage. | P0 |
| F17 | Preserve the ICC colour profile, and keep EXIF metadata on JPG output. | P1 |
| F18 | Accept files dropped on the app icon (Dock on macOS, the .exe or taskbar on Windows) and files passed on launch. | P1 |
| F19 | "Reveal in Finder/Explorer" for a converted file in the result list. | P1 |
| F20 | File > Open... picker as a non-drag alternative. | P1 |
| F24 | A separate Settings window (gear button, Cmd+, on macOS, Ctrl+, on Windows) holds all settings: output format, JPG quality, and update options. The gear and its shortcut are enabled only while the main window is ready for files (section 5). | P0 |
| F25 | Update check: a "Check for Updates..." menu item, plus an automatic check at launch at most once per 24 hours, on by default and switchable in Settings. The check sends nothing about the user or their files. | P0 |
| F26 | Update install: download, verify the signed update manifest against a public key built into the app (Authenticode is not available, since Windows builds ship unsigned), install and relaunch. Only install when no conversion is running. The user can postpone or skip a version. A failed update never blocks the app. | P0 |
| F27 | Decoders sit behind a plug-in interface (Pillow built in, pillow-heif for HEIC and AVIF), so new input formats such as camera RAW can be added without touching the UI, naming or output code. | P0 |
| F28 | Platforms: macOS on Apple Silicon and Intel, Windows on x64 and ARM64. | P0 |
| F29 | Camera RAW input (via rawpy/LibRaw), through the F27 interface. | P2 |
| F30 | Optional "replace original" mode for in-place conversion. If added, the original goes to the Trash or Recycle Bin, never permanently deleted. | P2 |
| F31 | Stop: while a batch runs and more than one file is queued, a Stop button finishes the file in hand, discards the rest, and reports "Stopped after 3 of 12" with the number not converted. No output is ever left half written. | P0 |
| F32 | Details window: a separate, non-modal window listing every file in the batch with its result, output name and before/after size. It opens from the Details button, closes with Esc or Close, and closes when a new batch starts. | P0 |

*F21 to F23 (the optimise prompt, the ` optimised` suffix and the "already optimal" rule) were withdrawn in revision 3. F8 replaces them: conversion is unconditional and driven entirely by the current settings. Requirement numbering is unchanged so existing references elsewhere stay valid.*

## 5. UX and UI specification

One main window, a Settings window, and a Details window. The main window holds a single area, the stage, and the stage shows exactly one of three states: ready, progress or result. There is no status bar, and no message ever appears below the stage.

**Layout**

1. **Stage** fills the window above a fixed strip at the bottom. Its content changes with the state.
2. **Bottom strip**, fixed height, holds the gear at the right. It is always present, so no state change can move the stage. An update notice, when that feature is added, sits in this strip beside the gear and never interrupts a running batch.
3. Nothing else.

Suggested default window size: about 520 x 470 px, resizable, with a minimum of 420 x 390.

**Settings control**

The gear is always visible and is enabled only while the window is Ready. Settings are read when a batch starts, so a change cannot affect files already on screen; offering the control there would promise something the app cannot do.

| Main window state | Gear | File > Settings and Cmd/Ctrl+, |
| --- | --- | --- |
| Ready, including while a file is dragged over the window | Shown, enabled | Enabled |
| Progress, stopping | Shown, disabled | Disabled |
| Any result state | Shown, disabled | Disabled |
| Details window open | Follows the main window: disabled while a result is on screen, enabled once the result is dismissed | Same as the gear |

- Disabled rather than hidden: hiding it would collapse the strip and move the stage, which is the jump this layout exists to prevent.
- One flag drives the icon, the menu item and the shortcut, so the three can never disagree.
- A Settings window already open when a batch starts stays open; its changes apply to the next drop.

**The three states**

| State | On screen | Ends when |
| --- | --- | --- |
| Ready | Dashed outline, "Drop images here", "or click to choose files", and the setting line "Converts to JPG, quality 90", which opens Settings | a drop arrives |
| Progress | No outline. "Converting 3 of 12", the file name, a slim bar, and Stop | the last file finishes |
| Result | No outline. An icon, a headline, one line of detail, and buttons | OK, a new drop, or three seconds for a clean success |

The dashed outline is a drop instruction, so it appears only while it means something: in the ready state, and while a file is dragged over the window in any state.

**Progress rules**

- One file at a time. "Converting 3 of 12" counts the file in hand.
- With a single file it reads "Converting…" with the file name and no bar, because a bar across one file measures nothing.
- A drop during progress joins the queue, and the total grows.
- Stop finishes the file in hand, discards the rest, and reports "Stopped after 3 of 12" with "9 not converted".
- Stop is hidden when one file remains, because it could not be honoured without abandoning a half-written file.

**Result rules**

| Outcome | Icon | Headline and detail | Buttons | Clears |
| --- | --- | --- | --- | --- |
| All converted | Green tick | "5 converted", then "1.2 MB smaller" | none | after three seconds |
| Some skipped or failed | Amber triangle | "4 converted, 1 skipped", then the reason | Details, OK | on OK or a new drop |
| Nothing converted | Red cross | "Nothing converted", then the reason | Details, OK | on OK or a new drop |
| Stopped by the user | Amber triangle | "Stopped after 3 of 12", then "9 not converted" | Details, OK | on OK or a new drop |
| Nothing usable in the drop | Amber triangle | "Nothing to convert", then "No supported images in that drop." | OK | on OK or a new drop |

- The detail line explains the common case without a click. With exactly one problem file it names it and the reason ("notes.txt — not a supported image"); with more than one it says "Open Details for the reasons".
- OK returns to Ready. Esc does the same. Return presses the default button.
- A new drop at any point replaces the message and starts converting.
- A larger output is kept (F8), so the clean result says "Saved beside the originals" and the exact sizes are in Details.

**Pictograms**

Icons come from Lucide (ISC licence, notice in `THIRD_PARTY_NOTICES.md`). They are painted from their path data at any size and colour, so light, dark and disabled states need no extra files.

| Where | Icon | Size | Stroke |
| --- | --- | --- | --- |
| Settings gear | `settings` | 32 px | 1.5 px |
| Converting, stopping | `clock` | 72 px | Lucide's 2 units, about 6 px here |
| All converted | `file-check` | 72 px | same |
| Skipped, failed, stopped, nothing usable | `triangle-alert` | 72 px | same |
| Nothing converted | `file-x` | 72 px | same |

- Colour: the gear uses the window text colour, faded when disabled. The status icons use green, yellow and red, each with a light-theme and a dark-theme value, because a thin stroke needs more contrast on white than on black.
- Progress and Result share a fixed icon slot of 80 px and a fixed action slot of 48 px, so moving between them moves nothing on screen. Ready has no icon.
- The stroke width was set only for the gear. The large icons keep Lucide's own stroke.

**Details window**

- A separate, non-modal window opened by Details. One at a time, rebuilt for each batch, and closed when a new batch starts.
- A table of every file in the batch: File, Result, Output, Size.
- Double-clicking a converted row, or the Show in Finder button, reveals that file.
- Closes with Esc or Close, and never blocks the main window.

**Settings window**

Opens from the gear button, or with Cmd+, (macOS) and Ctrl+, (Windows), and only from the Ready state (see Settings control). One instance, not modal. Every change saves immediately, so there is no OK or Cancel. Closes with Esc or Cmd/Ctrl+W, and the main window reflects changes at once.

| Group | Control | Details |
| --- | --- | --- |
| Output | Format: JPG or PNG | Segmented control. Default JPG. |
| Output | JPG quality | Slider plus numeric field, 1 to 100, default 90, with a hint that lower means smaller files and more visible compression. When PNG is selected the row is replaced by one line: "PNG is lossless, so there is no quality setting." The stored value is kept for the next time JPG is chosen. |
| Updates | Check for updates automatically | Checkbox, on by default. A "Check now" button and the current version beside it. |
| About | Version, licences, privacy | Version and licence line, then: "No account and no tracking. imgIO never sends anything about you or your images. The only network request it makes is the update check, which you can turn off." The Settings footer reads "No account. No tracking." |

**Buttons**

Every button locks itself on the click, before the action runs, so no command can be sent twice. This is both status feedback and error prevention.

1. On click the button disables itself first, then the action runs.
2. If the action takes time, the button says so in its own words: Stop becomes "Stopping…", Check now becomes "Checking…".
3. A disabled button cannot be pressed again with the mouse, Return or Space.
4. It re-enables only when the state it started has finished. If the screen it belonged to is gone, it disappears rather than coming back.
5. Actions fire on the release of the click, so pressing and dragging off the button cancels. That matches macOS and protects Stop in particular.

| Button | On the click | Result |
| --- | --- | --- |
| Stop | Disabled at once; the stage becomes "Stopping…" and "Finishing the current file", and all buttons leave | No second stop, no repeated cancel |
| OK | Disabled at once; the stage returns to Ready | No double dismiss |
| Details | Disabled until the window is up; if a Details window is already open it is raised instead of a second one opening | One Details window |
| Gear | One Settings window; a second click raises it | One Settings window |
| Check now (updates, later) | Disabled and labelled "Checking…" until the answer arrives | No repeated checks |

**Platform behaviour**

- Follow the system light and dark appearance and the system accent colour.
- macOS: standard app menu (About, Settings..., Check for Updates..., Quit), Cmd+, Cmd+O and Cmd+Q. Windows: a gear button and a Help menu entry for updates, Ctrl+, and Ctrl+O. Settings is enabled only while the window is ready for files.
- Quality changes apply from the next drop, never to files already converted.
- Keyboard path: Open... (F20) lets users without a pointer convert files too.

## 6. Technology recommendation

PySide6 (Qt for Python) holds up as the best fit after comparing the alternatives, so build v1 with PySide6 + Pillow. Treat this as a recommendation, not a mandate: the developer should confirm it in a one-day proof of concept (drop a file, convert, build an unsigned package on both OSes) before committing.

**Framework comparison**

| Option | UI approach | Fit for this utility | Main drawback |
| --- | --- | --- | --- |
| **PySide6 (Qt Widgets)** | Qt widgets styled to match each OS | Recommended. Drag and drop is built in, Python has the best imaging libraries, one codebase. | Larger bundle (a reported PySide6 tool shipped at 118 MB); widgets imitate native look rather than being OS controls. |
| PyQt6 | Same Qt | Same technically. | GPL or paid commercial licence; PySide6 is LGPL, which allows closed-source distribution. |
| Qt with C++ | Same Qt | Smallest and fastest result. | Higher development cost; image handling needs more code. |
| Tauri | System web view with a web UI | Small installer, but the UI is HTML, not native widgets. | Needs Rust plus web skills; conflicts with the "native UI" requirement. |
| Electron | Bundled Chromium with a web UI | Mature, but the heaviest for a tiny utility. | Large download for a small job; not native UI. |
| SwiftUI (macOS) + WinUI (Windows) | Truly native controls | Best platform fidelity. | Two codebases and two skill sets for a one-screen app. |

The assessment column is my judgement; the size anecdote, the licensing difference and the Electron/Tauri architecture are from the sources listed at the end.

**Versions.** PySide6 6.11 shipped in March 2026; Qt 6.12 LTS was released on 30 September 2026. Verified on PyPI on 16 Nov 2026: PySide6 6.12.0 publishes `macosx_14_0_universal2`, `win_amd64` and `win_arm64` wheels and declares Python 3.10–3.15. **The effective Python floor is 3.11, not 3.10**, because Pillow 13.0.0 requires `>=3.11`. **Pin an exact 6.12 version.** That fixes the minimum macOS at 14 and the minimum Python at 3.11.

**Imaging library.** Use Pillow for decoding, EXIF orientation (`ImageOps.exif_transpose`), colour-mode conversion and saving, with `pillow-heif` registered for HEIC and AVIF (required in v1). Pillow identifies files by content rather than extension, which F6 relies on. Camera RAW is planned for later, and `rawpy` (a Python wrapper around LibRaw) is the likely route: the wrapper is MIT-licensed, and its repository also carries LibRaw's LGPL-2.1 licence file. Keep every decoder behind the plug-in interface (F27) so adding RAW touches nothing else. Check the licences of all native libraries bundled in the wheels (libheif, LibRaw) during release prep.

**Suggested structure**

- `core/convert.py`: UI-free `convert(path, fmt, quality) -> Result`, used for every input including files already in the output format. Unit-testable on its own.
- `core/decoders/`: a decoder registry behind one interface. Pillow first, HEIC in v1, camera RAW later.
- `core/naming.py`: target-name and collision logic (F4), including the case-insensitive and Unicode-normalised comparison.
- `ui/`: main window, drop zone widget (`QDropEvent`, accept only local file URLs), result list, and the Settings window.
- `updates/`: an `UpdateService` interface (check, download, verify, apply) so the update backend can change without touching the UI. The version number has one source of truth.
- Worker: a `QThreadPool`/`QRunnable` (or single `QThread`) that emits progress and result signals to the UI.
- Write each output to a temporary file in the destination folder, then rename it to the final name, so a crash or full disk never leaves a half-written image.

**Packaging.** Qt's deployment docs list `pyside6-deploy` (Nuitka-based), PyInstaller, cx\_Freeze and others; note that `pyside6-deploy` is a command shipped inside PySide6, not a separate PyPI distribution. PyInstaller 6.22.3 supports Python 3.14. Try two of them in the proof of concept. Prefer folder-style (one-dir) builds over single-file executables: it keeps the Qt libraries replaceable, which LGPL compliance discussions in the Qt community turn on. Because the app is open source, LGPL compliance is simpler, since the source is public. Still ship the required licence notices and check the licences of the native libraries bundled in the wheels. Produce a `.app` inside a `.dmg` on macOS and an installer (Inno Setup or NSIS) or signed zip on Windows.

**Two macOS builds, not one universal2 bundle.** PySide6 6.12 ships a universal2 macOS wheel, but Pillow 13.0.0 and pillow-heif 1.8.1 publish architecture-specific macOS wheels only (arm64 and x86_64, with no universal2). A universal2 `.app` would require merging the native extensions by hand, so v1 ships one arm64 build and one x86_64 build, which section 7 already allows. Consequences: two notarization runs, two assets per release, and an updater that selects the correct architecture.

**Updates (required in v1).** The requirements are in F25 and F26. They are about behaviour, not about a library: a "Check for Updates..." item and an automatic launch check that can be turned off; a signed feed hosted with the releases; a signature check before anything is installed; install and relaunch only when no conversion is running; and failures that never block the app. Two backends are on the table before choosing:

- **Sparkle on macOS and WinSparkle on Windows.** Mature native update frameworks with Python wrappers ([SparkleHelper](https://pypi.org/project/SparkleHelper/), [pywinsparkle](https://pypi.org/project/pywinsparkle)). Verified 16 Nov 2026: **pywinsparkle is effectively dead**, last released in April 2019 with wheels for CPython 2.7 and 3.3–3.7 only, so it cannot run on the pinned Python. SparkleHelper is 0.1.2 (July 2026) — real, but pre-1.0. Caveats remain: the Sparkle wrapper needs a Nuitka build and Sparkle needs a packaged `.app` bundle. WinSparkle itself is still reachable through `ctypes` if this route is wanted.
- **tufup.** One cross-platform Python updater built on The Update Framework, and [it works with any app bundle, not only PyInstaller](https://pypi.org/project/tufup/). Verified 16 Nov 2026: 0.10.0, pure Python, no platform constraints.

**How the update check works**

1. **Release.** CI builds and signs each release, uploads the installers to a public location (GitHub Releases or the project website), and publishes a small feed file listing the latest version, download URL, checksum, signature and release notes. The feed is signed with the update-signing key.
2. **Check.** On launch, at most once per 24 hours (and whenever the user picks "Check for Updates..."), a background thread fetches the feed over HTTPS and compares its version with the running version. Nothing about the user or their files is sent.
3. **Notify.** If the feed has a newer version, a notice beside the gear shows the version number and release notes with three choices: Install, Later, Skip this version. Nothing downloads without the user choosing Install.
4. **Download and verify.** The installer downloads to a temporary folder. The app checks its signature against a public key built into the app, and refuses to install anything that fails.
5. **Install.** The app waits until no conversion is running, then closes, applies the update (macOS replaces the app bundle; Windows runs the per-user installer silently) and relaunches the new version.
6. **Failure.** If any step fails, the old version stays in place and keeps working. Automatic checks fail silently, and a manual check shows a plain message.

Whichever is chosen: CI publishes the update feed with each release, the update-signing private key lives only in CI secrets or offline, and on Windows the app installs per user (no admin rights) so updates can apply without a prompt. Test early whether an installer fetched by the updater still triggers SmartScreen on Windows.

**Licence: MIT.** MIT is the simplest permissive licence and the usual default when there is no reason to require copyleft. PySide6's LGPL does not dictate the app's licence: its duties concern PySide6 itself (ship its licence text, offer its source, keep it replaceable), not the app's own code. Use Apache-2.0 instead only if an explicit patent grant matters, and GPL-3.0 only if every fork must stay open source. Whichever is used: a single OSI-approved licence, a `LICENSE` file at the repository root, and a `THIRD_PARTY_NOTICES` file listing Qt/PySide6 (LGPLv3), Pillow, pillow-heif and libheif, and later rawpy and LibRaw. The developer verifies each bundled library's licence.

## 7. Platform specifics

macOS must be signed and notarized. Windows v1 ships unsigned: the owner has accepted the SmartScreen warning, and signing can be added later without changing the app.

**macOS**

- Distribute outside the Mac App Store. Apps downloaded this way need a Developer ID Application certificate (the owner already holds an Apple Developer Program membership, so there is no new cost; the developer will need the owner to create the certificate and an app-specific password or API key for notarization) and notarization, or Gatekeeper blocks them.
- PyInstaller-built apps typically need hardened-runtime entitlements to pass notarization; budget time for this.
- Handle `QFileOpenEvent` so files dropped on the Dock icon reach the app (F18).
- The Mac App Store sandbox will likely block writing files beside dropped originals. Verify before ever considering that route.
- Ship both Apple Silicon and Intel, as two separate builds rather than one combined build, because Pillow and pillow-heif ship separate files per chip type. Both builds have a minimum of macOS 14.

**Windows**

- Windows builds ship unsigned in v1 (the owner accepts the SmartScreen warning). Document the first-run workaround in the README and on the download page (SmartScreen: choose More info, then Run anyway), and publish checksums so users can verify the download. Later options if the warning hurts adoption: SignPath Foundation (free for open source, requires an OSI-approved licence with no dual-licensing and builds made from the public repo), Azure Artifact Signing, an OV certificate, or the Microsoft Store as a second channel. Unsigned builds trigger a SmartScreen "unrecognised app" warning. EV certificates no longer give instant SmartScreen trust, so even signed builds may show a warning until reputation builds.
- Ship x64 and ARM64 builds. PySide6 publishes Windows ARM64 wheels; check the same for pillow-heif (and later rawpy). Build and test each on matching hardware or a runner.
- Install per user (no admin rights) so the updater can apply updates silently.
- Files dropped on the `.exe` arrive as command-line arguments; parse them at startup (F18).
- Support Unicode and long paths. Test files on OneDrive and network drives.

**Minimum OS version: macOS 14.** It is set by the pinned PySide6 6.12 release. The older 6.11 would reach macOS 13, but it was rejected to stay on the longer-supported line. State the minimum in the README. Intel Macs that cannot run macOS 14 are out of scope, so the Intel test machine must be on macOS 14 or later.

## 8. Non-functional requirements

- **Responsiveness.** The UI thread never decodes or encodes images. Dropping 100 files must not freeze the window.
- **Performance.** Meet the targets in section 2. Process files one at a time (or a small pool) to cap memory.
- **Large images.** Define a supported ceiling of at least 100 megapixels. Pillow raises a decompression-bomb warning and error on very large images by default, so handle that explicitly: convert legitimate large photos, report the file as failed if it is still refused. Do not crash.
- **Reliability.** Atomic writes (temporary file, then rename). If anything fails mid-file, remove the temporary file and leave the source untouched.
- **Privacy.** No telemetry and no account. The only network request is the update check (F25), which fetches a signed feed and sends nothing about the user or their files, and can be turned off. Say so in the About box.
- **Accessibility.** All controls keyboard-reachable, labelled for screen readers (VoiceOver, Narrator), readable at high DPI and in dark mode, and a non-drag path through Open... (F20).
- **Logging.** Write a local rolling log file for support, with paths and error messages and no image content.
- **Localisation.** English only in v1, but keep all user-visible strings in one place.

## 9. Edge cases and error handling

Every failure is reported per file in the result list. One bad file never stops the rest of the batch.

| Case | Required behaviour |
| --- | --- |
| Corrupt or truncated image | Mark failed, "File could not be read". Continue. |
| Unsupported file (PDF, video, text) | Mark skipped, "Not a supported image". |
| Wrong or missing extension | Identify by content. A `.jpg` that is really a PNG converts normally. |
| Source already in target format | Re-encode it at the current setting (F8). The output name collides with the source and takes the `(n)` suffix; the original is untouched. |
| Target name already exists | Add ` (1)`, ` (2)` and so on (F4). Never overwrite. |
| Target name differs from an existing file only by case | Treat it as taken: `Photo.jpg` blocks `photo.jpg`. Append `(n)` using the source's casing (F4). |
| Transparent PNG, GIF or WebP to JPG | Flatten onto white (F12). |
| Animated GIF or WebP | Convert the first frame only and note it in the result. |
| CMYK, grayscale or 16-bit source | Convert to a suitable RGB (or grayscale) 8-bit mode for the output. |
| EXIF-rotated photo | Output upright, no double rotation (F13). |
| Very large image | See section 8. Fail gracefully, never crash. |
| Read-only or protected folder | Fail with "Can't write to this folder". Do not fall back to another folder silently. |
| Disk full or write error | Delete the temporary file, report failure, source untouched. |
| Source locked by another app (Windows) | Report "File is in use". |
| Cloud-only file (iCloud, OneDrive) | Reading may trigger a download. Show "Converting" status rather than appearing frozen. |
| Files dropped while a batch runs | Queue them. |
| Same file dropped twice | Convert twice; the second pass gets a collision suffix. |
| Folder dropped | Convert supported images directly inside it (F14). Ignore hidden files and subfolders. |
| Non-ASCII, very long or network paths | Must work on both platforms. |
| Re-encoding produces a larger file | Keep it (F8). Report both sizes in the result summary. |
| Update ready while a batch is running | Wait until the queue is idle before installing (F26). |
| Update feed unreachable, or an update fails signature verification | Unreachable: stay silent on automatic checks, say so on a manual check. Failed verification: refuse to install and warn the user. |

## 10. Acceptance criteria, test plan, milestones and open questions

**Acceptance criteria**

- Given 5 PNG files in a folder and the setting JPG/90, when I drop them on the window, then 5 `.jpg` files appear in that folder within a few seconds and the PNGs are unchanged.
- Given `a.jpg` already exists, when I convert `a.png`, then `a (1).jpg` is created and `a.jpg` is untouched.
- Given PNG is selected, when I drop a JPEG, then a `.png` is created and the quality control is disabled.
- Given a transparent PNG and JPG output, then the result has a white background and no black halo.
- Given a phone photo shot in portrait, then the output opens upright in a standard viewer.
- Given one corrupt file among ten, then nine convert and the summary names the failed one.
- Given 3 PNGs dropped and all converted, then a green tick and "3 converted" appear in the same area, nothing is shown below it, and the window is back to Ready three seconds later.
- Given a drop containing one unsupported file, then "2 converted, 1 skipped" and the file's name and reason stay until OK is pressed, and Details opens a separate window listing every file.
- Given 5 files dropped and Stop pressed while the second file is being written, then that file finishes, the remaining three are untouched, and the message reads "Stopped after 3 of 5" with "2 not converted".
- Given a batch runs, when I drop more files, then they queue and the total in "Converting 3 of 8" grows; nothing is refused.
- Given the last result shown, when I press Esc, then the window returns to Ready.
- Given 5 files dropped and Stop pressed twice in quick succession, then the button disables on the first click, the second does nothing, and one result appears: "Stopped after 3 of 5".
- Given a batch is running, then the gear is greyed out, Cmd+, does nothing, and the stage does not move when the batch ends.
- Given a batch finishes, then the clock is replaced by the green tick without any text moving, and the gear stays greyed until OK is pressed.
- Given PNG is selected, then no quality control is on screen, one line explains why, and switching back to JPG shows the quality value I had.
- Given the app is quit and relaunched, then format and quality are as I left them.
- Given a HEIC photo, then a JPG is created and opens upright.
- Given JPG/50 is selected and 3 PNGs plus 2 JPGs are dropped from one folder, then 5 new `.jpg` files appear beside their sources at quality 50, each source JPEG gains a `(n)` suffix (`photo.jpg` yields `photo (1).jpg`), and all 5 originals are byte-identical afterwards.
- Given JPG/90 is selected and a JPEG already saved at a low quality is dropped, then the output is kept even if it is larger, and the summary reports both sizes.
- Given the Settings window is open, when I change the quality, then the main window's setting line updates at once with nothing to confirm.
- Given a newer version in the update feed, when the app launches with automatic checks on, then a notice appears, and Install downloads, verifies and relaunches into the new version.
- Given a tampered update package, then installation is refused with a warning.
- Given a batch is running when an update becomes ready, then the update waits until the batch finishes.

**Test plan**

- Unit tests for the convert and naming modules using a fixture set: PNG with alpha, 16-bit PNG, CMYK JPEG, EXIF-rotated JPEG, a JPEG saved at low quality, an already-optimally-encoded JPEG and PNG, animated GIF, WebP, TIFF, HEIC, corrupt file, 0-byte file, a 100 MP image.
- Manual matrix: macOS on Apple Silicon and Intel, Windows on x64 and ARM64, each on a fresh user account or VM using the packaged build, not only a dev run.
- Update tests: serve a local test feed, upgrade from the previous version to the new one on all four targets, and test a tampered package and an unreachable feed.
- Drag sources: Finder, Explorer, desktop, Downloads, a network share, OneDrive/iCloud folders, a read-only folder.
- Install check: first launch of a downloaded build shows only the expected first-run prompts (the Windows SmartScreen warning is accepted and documented).

**Milestones**

1. Proof of concept: a PySide6 window with a drop zone, one Pillow conversion and one HEIC conversion, packaged on all four targets. In the same proof of concept, try both packaging tools and confirm wheel availability for Intel Mac and Windows ARM64.
2. Core: the convert and naming modules plus the decoder registry, with unit tests (F3 to F8, F12, F13, F27).
3. UI: main window, Settings window, background worker, result list (F9 to F11, F15, F16, F24).
4. Updates: `UpdateService`, feed publishing in CI, signing keys, tested upgrade path (F25, F26).
5. P1 features: folder drop, app-icon drop, metadata, Open... (F14, F17 to F20).
6. Release engineering: macOS signing and notarization, Windows installers (unsigned), README with the SmartScreen workaround and checksums, `LICENSE` and `THIRD_PARTY_NOTICES`, About box, public repository.
7. Beta on all four targets, fix, ship. Camera RAW (F29) follows as a later release.

**Proof of concept results (16 Nov 2026)**

Built and run on the Apple Silicon development machine (macOS 15.6.1, Python 3.14.4, PySide6 6.12.0, Pillow 13.0.0, pillow-heif 1.8.1). The window accepts drops, converts on a background thread, writes beside the source and never overwrites. Verified conversions of PNG (with transparency), JPEG, HEIC and an unsupported text file, in both the source run and the packaged apps.

| Packaging tool | Build time | App size | Runs | Notes |
| --- | --- | --- | --- | --- |
| PyInstaller 6.22.3 | 10 s | 97 MB | Yes | Simple; needs `--collect-all pillow_heif`; bundle tags macOS 14. |
| Nuitka 4.3.5 | several minutes | 101 MB | Yes | Works, but compiles to a macOS 15.0 minimum unless `--macos-deployment-target=14.0` is passed. |

- The official `pyside6-deploy` command (6.12.0) fails on an Essentials-only install: its Nuitka plug-in requires the full `PySide6` distribution. It also pinned Nuitka 4.1.1, which treats Python 3.14 as experimental.
- **PyInstaller is the choice for v1.** Both tools produce a working app; PyInstaller builds in seconds, ships smaller, and needs no extra flag to keep the macOS 14 floor. Nuitka remains a fallback if startup speed or anti-virus false positives later prove to be a problem.
- Only `PySide6-Essentials` is installed. The full `PySide6` package adds Qt WebEngine, about 250 MB the app never uses.
- The Windows and Intel builds are not yet produced; they need those machines or a runner.

**Decided**

- HEIC input is required in v1. Camera RAW comes later, so decoders are plug-ins.
- **Only controls that apply are shown (revision 11).** When PNG is selected, the quality row is replaced by one sentence rather than disabled. A control that cannot do anything in the current mode reads as broken, not as unavailable, and the window keeps its height so nothing jumps. "No telemetry" is replaced by plain wording in the interface: "No account. No tracking."
- **Pictograms are Lucide, painted from path data (revision 10).** Lucide is ISC licensed, so it can live in a public MIT repository as long as its notice ships in `THIRD_PARTY_NOTICES.md`. Drawing from path data keeps every icon crisp, theme-aware and free of image files. Status marks use green, yellow and red with a light-theme and a dark-theme value; the stroke width was specified only for the 32 px gear.
- **Every action button locks on click (revision 9).** The click disables the button before the action runs, an action with a duration says so in the button's own words, and re-enabling waits for the state to finish. A disabled button cannot be triggered twice.
- **The gear belongs to the ready state (revision 8).** It sits in a fixed strip at the bottom, is always visible, and is enabled only while the window accepts files. Disabling rather than hiding it keeps the strip from collapsing and moving the stage, and one flag drives the icon, the menu item and the shortcut so they cannot disagree.
- **The window has one area (revision 7).** It shows ready, progress or result, never two at once. There is no status bar and no message below the stage; the per-file list lives in its own window (F32). The dashed outline is a drop instruction, so it is drawn only in the ready state and during a drag hover.
- **Results split by whether they need attention.** A clean conversion clears itself after three seconds. Anything skipped, failed or stopped waits for OK or a new drop, because it is information the user asked for by dropping the file.
- **Stop finishes the file in hand** rather than interrupting it, so no output is ever left half written. It is offered only when more than one file is queued.
- **Conversion is unconditional (revision 3).** Every supported input produces exactly one output at the current format and quality. Files already in the target format are re-encoded like any other, so there is no optimise prompt, no skip path, no ` optimised` suffix, no "already optimal" rule and no "existing files" setting. The product is a converter.
- **A larger output is kept.** If re-encoding grows the file, the output stays and the summary reports both sizes. The app cannot know a source's JPEG quality, because no file format stores one, so it never guesses; it applies the setting.
- Licence: MIT, with a `THIRD_PARTY_NOTICES` file (reasoning in section 6).
- Updates are in scope: a check, a signed feed, and verified install (section 6 explains the steps).
- All four targets are supported: macOS on Apple Silicon and Intel, Windows on x64 and ARM64.
- Qt widgets count as native enough for now.
- Settings live in a separate window.
- Windows v1 ships unsigned; macOS is signed and notarized.
- **The app is named imgIO.** The owner and developer is Vishal Gupta.
- **Output naming is one rule** (F4): target `<stem>.<ext>`; on collision `<stem> (1).<ext>`, `<stem> (2).<ext>`, incrementing until a free name is found; exactly one space before the `(`. There is no separate suffix for any path. The doubled spaces in revision 1 were Markdown padding, not literal.
- **Owner identity and credentials.** The owner holds an Apple Developer Program membership and will supply the Developer ID certificate and notarization credentials (an app-specific password or API key) when they are needed.
- **SmartScreen accepted.** Windows v1 ships unsigned; the owner accepts the warning, and the bypass is documented in the README and on the download page.
- **Hardware.** An Apple Silicon Mac on macOS 15.6.1 is the development machine. An Intel Mac is available for testing. There is no Windows ARM64 machine yet; one can be arranged and is not treated as a blocker.
- **Dependency availability is confirmed** (PyPI, 16 Nov 2026): PySide6 6.12.0, Pillow 13.0.0 and pillow-heif 1.8.1 all publish macOS arm64, macOS x86_64 and Windows arm64/amd64 wheels, so every format in F7 and every platform in F28 is reachable. Pillow and pillow-heif have no universal2 macOS wheels, so macOS ships two builds (section 6).
- **Minimum macOS is 14, with PySide6 6.12 pinned.** The older 6.11 would support macOS 13, but was rejected to stay on the longer-supported line. Intel Macs that cannot run macOS 14 are out of scope, so the Intel test machine must be on 14 or later.
- **Case-insensitive collisions are settled (F4).** Existing names are compared ignoring case and Unicode normalisation, so the same drag produces the same filenames on case-sensitive and case-insensitive volumes. The output stem keeps the source's exact casing: `Photo.png` gives `Photo.jpg`, or `Photo (1).jpg` if taken; `photo.png` gives `photo.jpg`, or `photo (1).jpg`. Extensions are always lowercase. The cost, accepted: on a case-sensitive volume a technically free name is skipped rather than risk overwriting `Photo.jpg`.
- **PyInstaller is the packaging tool** (revision 5), on the measurements in section 10. Nuitka stays a fallback. The app installs only `PySide6-Essentials`, not the full `PySide6` package.
- **Python floor is 3.11**, set by Pillow 13.0.0, not 3.10 as revision 1 stated.

**The developer decides during the proof of concept**

- **Library availability.** Confirmed for Pillow and pillow-heif on all four targets (see Decided). rawpy wheels for Intel Mac and Windows ARM64 remain to be checked when camera RAW is added; report back before dropping a format or a platform.

**Deferred: decide when that work starts, not before**

- **Which update library.** Nothing else depends on it, so it is not a blocker and needs no decision now. When auto-update work starts, `tufup` is the default because the Windows Python bridge for Sparkle/WinSparkle has not been updated since 2019 and cannot run on modern Python. Revisit only if `tufup` fails a short test at that point.

**Later**

- Camera RAW: which formats first, and whether to use the embedded preview or a full develop.
- "Replace original" mode (F30): not in v1. If added, originals go to the Trash or Recycle Bin.

## Sources

As of 16 Nov 2026.

- [PySide6 6.11.0 on PyPI (released 23 Mar 2026, Python 3.10+)](https://simple-repository.app.cern.ch/project/pyside6)
- [Qt for Python blog: Qt 6.12 LTS released, 30 Sep 2026](https://www.qt.io/blog/tag/qt-for-python)
- [PyQt6 vs PySide6 licensing (GPL or commercial vs LGPL)](https://www.pythonguis.com/faq/licensing-differences-between-pyqt6-and-pyside6/)
- [PySide6 vs Electron: 118 MB tool vs 250 MB (one developer's report)](https://dev.to/kerfiq/pyside6-vs-electron-why-i-shipped-a-118-mb-windows-desktop-tool-not-a-250-mb-cross-platform-one-2gfl)
- [Electron vs Tauri architecture: Chromium vs system web view](https://ph.pollub.pl/index.php/jcsi/article/download/7831/5150/36462)
- [Qt for Python deployment tools (pyside6-deploy, PyInstaller, cx\_Freeze and others)](https://doc.qt.io/qtforpython/deployment/index.html)
- [Qt forum: LGPL obligations when packaging PySide6 apps](https://forum.qt.io/post/790010)
- [Pillow image file formats handbook (format detected from contents)](https://pillow-docs-cn.readthedocs.io/zh-cn/latest/handbook/image-file-formats.html)
- [pillow-heif on PyPI (HEIC and AVIF support for Pillow)](https://redirect.github.com/bigcat88/pillow_heif)
- [electron-builder code signing: Developer ID, notarization, SmartScreen, EV change](https://www.electron.build/docs/features/code-signing/)
- [Code signing overview: $99/year Apple Developer, notarization required](https://learnwithhasan.com/boilerplates/electron-starter-template/docs/code-signing/)
- [Signing and notarizing a PyInstaller macOS app (entitlements)](https://haim.dev/posts/2020-08-08-python-macos-app)

* [PySide6 6.12.0 on PyPI: Windows ARM64 and macOS universal2 wheels](https://pypi.org/pypi/PySide6)
* [PySide6 6.11.0 wheels: macOS 13+ universal2 and Windows ARM64](https://pypi.org/project/PySide6/6.11.0/)
* [SparkleHelper: Sparkle and WinSparkle for Python apps](https://pypi.org/project/SparkleHelper/)
* [pywinsparkle: WinSparkle wrapper for frozen Python apps](https://pypi.org/project/pywinsparkle)
* [tufup: updater for stand-alone Python apps](https://pypi.org/project/tufup/)
* [rawpy 0.27.0: MIT-licensed LibRaw wrapper](https://simple-repository.app.cern.ch/project/rawpy)
* [rawpy repository: MIT plus LibRaw's LGPL-2.1 licence file](https://github.com/ccl/rawpy)
* [Producing Open Source Software: choosing a licence](https://producingoss.com/en/license-choosing.html)
* [Microsoft: code signing options for Windows apps](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
* [Microsoft: SmartScreen reputation](https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation)
* [SignPath Foundation conditions for open-source projects](https://signpath.org/terms)
* PyPI JSON metadata read on 16 Nov 2026 for the wheel and version checks in section 6 and section 10: `PySide6` 6.12.0, `Pillow` 13.0.0, `pillow-heif` 1.8.1, `PyInstaller` 6.22.3, `Nuitka` 4.3.5, `tufup` 0.10.0, `pywinsparkle` 1.6.0, `SparkleHelper` 0.1.2.
