# SpriteSheet Maker - Handoff

## Product

SpriteSheet Maker is a standalone local tool for converting black-background VFX media into transparent Unity sprite sheets.

## Current Status

- Created Python project skeleton.
- Implemented reusable processing pipeline in `src/unity_vx_motion_master/processor.py`.
- Implemented frame loading in `src/unity_vx_motion_master/frame_source.py`.
- Implemented CLI in `src/unity_vx_motion_master/cli.py`.
- Implemented Tkinter desktop GUI in `src/unity_vx_motion_master/gui.py`.
- Implemented stable local Web UI in `src/unity_vx_motion_master/web_app.py` and `src/unity_vx_motion_master/web_static/`.
- Added `pyproject.toml` console entry points.
- Added macOS launch script: `Launch SpriteSheet Maker.command`, now launching the Web UI to avoid macOS Tkinter crashes.
- Added optional PyInstaller build script: `scripts/build_mac_app.sh`.
- Added managed asset folders:
  - `assets/input`
  - `assets/output`
  - `assets/previews`
  - `assets/temp`
  - `examples`
  - `tests`

## Implemented Rules

- Black or near-black pixels convert to transparent using:
  - Black Threshold, default `20`
  - Soft Edge, default `8`
  - Alpha Strength, default `1.0`
- All frames are analyzed after transparency processing.
- The alpha channels are merged to calculate one shared maximum bounding box.
- Every frame is cropped using that same bounding box.
- Every frame is then placed on the same output canvas.
- Default anchor is center.
- Sprite sheet output is transparent PNG.
- Metadata JSON is written next to the output PNG by default.

## Dependencies

Required:

- Python 3.9+
- Pillow
- imageio-ffmpeg, used to provide a bundled ffmpeg binary for `.mp4`, `.mov`, `.webm`, `.avi`

Optional fallback:

- ffmpeg on PATH

GIF and PNG/JPG inputs work without ffmpeg.

## Run Commands

GUI:

```bash
python3 run_web.py
```

macOS launcher:

```bash
./Launch\ Unity\ VX\ Motion\ Master.command
```

CLI:

```bash
PYTHONPATH=src python3 run_cli.py INPUT_FILE --output assets/output/sprite_sheet.png
```

Optional Tkinter fallback:

```bash
python3 run_gui.py
```

Note: On the user's macOS 14.6 machine, system Python/Tkinter aborted with `macOS 14 (1407) or later required, have instead 14 (1406)`. The default launcher was switched to the local Web UI because it avoids Tk entirely.

## Known Gaps / Next Work

- Drag-and-drop is not implemented yet.
- Video preview depends on ffmpeg availability.
- Native app bundle script exists, but no packaged `.app` has been generated in this workspace yet.
- Unity Editor integration is not implemented yet.
- Custom anchor point is not implemented yet; current anchors are center/top/bottom.
- Start/end time range is not implemented; current workflow uses start/end frame as requested for artists.
- Web UI uploads source files into `assets/input/`; large uploaded media should be reviewed before GitHub upload.

## Resource Management

- Put source media in `assets/input/`.
- Put generated sheets in `assets/output/`.
- Put temporary or visual QA files in `assets/previews/` or `assets/temp/`.
- Keep only small demo assets in Git.
- Before GitHub upload, review `.gitignore` for generated outputs and large raw videos.

## Verification

- Generated example GIF with `python3 examples/make_sample_gif.py`.
- Passed smoke test with `python3 -X pycache_prefix=/private/tmp/uvxmm_pycache tests/smoke_test.py`.
- Passed CLI export with `python3 -X pycache_prefix=/private/tmp/uvxmm_pycache run_cli.py examples/sample_vfx.gif --output assets/output/cli_sheet.png --columns 4 --padding 2`.
- Passed import check for GUI module.
- Reproduced user's macOS launcher issue: system Python/Tkinter aborted due OS version check (`macOS 14 (1407) or later required, have instead 14 (1406)`).
- Switched default launcher to local Web UI (`python3 run_web.py`).
- Verified Web API upload with `curl -F file=@examples/sample_vfx.gif http://127.0.0.1:8766/api/upload`.
- Verified Web API preview and export; generated `assets/output/web_test_sheet.png`.
- User reported MP4 preview did not run because ffmpeg was missing.
- Added `imageio-ffmpeg>=0.6.0` to dependencies and made frame loading prefer its bundled ffmpeg binary before PATH lookup.
- Updated macOS launcher to install requirements when either Pillow or imageio-ffmpeg is missing.
- Installed imageio-ffmpeg locally and verified `_find_ffmpeg()` resolves its bundled binary.
- Generated `examples/sample_vfx.mp4` and verified MP4 export with `python3 -X pycache_prefix=/private/tmp/uvxmm_pycache run_cli.py examples/sample_vfx.mp4 --output assets/output/mp4_test_sheet.png --columns 4 --padding 2`.
- User requested compact one-screen layout, visible progress, and export save path control.
- Updated Web UI density and constrained preview height so the page stays within one browser viewport on desktop; left controls can scroll internally if viewport is unusually short.
- Reworked `/api/preview` and `/api/export` into asynchronous jobs with `/api/job?id=...` polling.
- Added progress bar, percent text, and stage messages for decoding, background removal, crop bounds, canvas normalization, composing, and saving.
- Added `Save Folder` input. Relative folders resolve under project root; absolute macOS paths are used directly.
- Added `Choose` button backed by `osascript` folder picker via `/api/choose-output-dir`.
- Verified async preview job returned `state=done progress=100`.
- Verified async export job generated `/Users/bytedance/Documents/Codex 2026/SpriteSheet Maker/assets/output/async_export_sheet.png` with 16 frames.
- User reported preview completed but image did not display, and requested two layout modes.
- Added static asset cache busting (`app.js?v=20260604-layout2`) plus no-cache headers for served files.
- Added preview image load/error handling in Web UI.
- Added FPS Preset selector: Original, 8 FPS, 12 FPS, 24 FPS, 30 FPS, Custom.
- Added Layout Mode selector:
  - `FPS Auto Grid`: uses selected FPS and auto-fits columns from Max Texture and frame cell width when Columns is empty.
  - `Custom Rows / Columns`: uses explicit Rows and Columns.
- Added `No blank cells: sample rows x columns frames`; when enabled, it samples exactly `Rows * Columns` frames evenly from the selected frame range.
- Added row support to `compose_sheet`, preserving old callers with keyword padding fixes.
- Fixed a regression where old positional `padding` arguments were interpreted as rows.
- Verified `Custom Rows / Columns` with no blank cells produced 35 frames, 7 columns, 5 rows.
- Verified `FPS Auto Grid` preview with 8 FPS returned a preview image and auto layout.
- User requested even frame and sheet dimensions.
- Added `even_size` and `ensure_even_canvas` in `processor.py`; frame canvas dimensions are rounded up to even sizes, and the final sheet is padded to even dimensions when needed.
- `place_on_canvas` now scales content down if a priority-derived cell is smaller than the crop.
- Added `Rows/columns priority` checkbox under no-blank grid. In Custom Rows / Columns mode, it derives an even cell size from Max Texture, Rows, Columns, and Padding instead of the Frame Canvas Width/Height.
- Verified priority mode with 7 columns, 5 rows, padding 3, Max Texture 512, and an intentionally oversized 999x999 canvas produced 35 frames, 70x100 frame cells, and a 508x512 sheet.
- Verified odd padding still exports an even sheet: `odd_padding_even_test.png` produced 104x104 frames and a 426x426 sheet.
- Updated smoke test to assert frame and sheet dimensions are even.
- User requested Chinese default UI with English toggle.
- Added top language toggle; Chinese is default, English is available by clicking `EN`.
- User requested Transparency to be folded by default while keeping Remove Black Background checked.
- Added a collapse control beside the Transparency title and set it collapsed by default.
- Removed `No blank cells` UI and merged its sampling behavior into `gridPriority`.
- Renamed the grid option to concise copy: Chinese `填满自定义行列`, English `Fill custom grid`.
- Removed the Download PNG button and stopped returning `downloadUrl` from job results.
- Reworked Save Folder button status and AppleScript folder picker invocation to make the macOS folder panel more likely to open reliably.
- Verified `Fill custom grid` export produced 35 frames, 70x100 frame cells, 7 columns, 5 rows, a 508x512 sheet, and no `downloadUrl` in the job response.
- User requested a `No padding / 无留白` option beside `Fill custom grid`.
- Added `tightGrid` UI option with Chinese `无留白` and English `No padding`.
- When `tightGrid` is enabled in Custom Rows / Columns mode:
  - Effective padding is forced to 0.
  - It samples `Rows * Columns` frames when rows and columns are provided.
  - The single-frame cell size is the unified maximum subject bounding box, rounded up to even dimensions.
  - The final sheet uses actual composed dimensions and only scales down if width or height exceeds Max Texture.
- Verified `tightGrid` 7x5 with input padding 9 and oversized canvas produced 35 frames, 104x104 frame cells, padding 0, and a 728x520 sheet.
- Fixed Max Texture scaling after even-size padding so the even-rounded cell cannot push the final sheet over the limit.
- Verified `tightGrid` 7x5 with Max Texture 512 produced 72x72 frame cells and a 504x360 sheet.
