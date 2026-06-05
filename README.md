# SpriteSheet Maker

SpriteSheet Maker is a local desktop tool for converting black-background VFX videos, GIFs, or still frames into transparent Unity-ready sprite sheets.

The core rule is animation-safe cropping: every frame is analyzed, all alpha bounds are merged into one shared bounding box, and every output frame uses that same crop and canvas. That prevents frame jitter during playback.

## MVP Features

- Input: GIF, PNG/JPG, and video formats supported by bundled/system `ffmpeg` (`.mp4`, `.mov`, `.webm`, `.avi`)
- Frame range: start frame, end frame, optional FPS resampling
- Transparency: black threshold, soft edge, alpha strength
- Unified crop: one maximum alpha bounding box across all frames
- Unified frame canvas: auto size or custom width/height
- Anchor: center, top, bottom
- Sprite sheet: auto/custom columns, per-frame transparent margin, max texture size scaling
- Output: transparent PNG, optional individual frames, optional metadata JSON
- Local Web UI: parameter panel, upload, preview composited over checker/black/white/gray backgrounds
- Async progress: Preview and Export show a live progress bar with stage messages
- Output folder: choose a macOS save folder or type a relative/absolute folder path
- Layout modes:
  - FPS Auto Grid: choose Original, 8, 12, 24, 30, or Custom FPS; columns are auto-fit from frame width and Max Texture when Columns is empty
  - Custom Rows / Columns: set exact rows and columns; `Fill custom grid` samples exactly `rows * columns` frames and fits cells from rows, columns, per-frame margin, and Max Texture
- Tight grid: `No margin` uses the unified maximum subject bounding box as each frame cell, forces the per-frame margin to 0, and only scales down if the final sheet exceeds Max Texture
- Even dimensions: each frame canvas and the final sprite sheet are forced to even width/height by adding transparent pixels when needed
- UI language: Chinese by default, with a top-left toggle for English
- Tkinter GUI: kept as an optional fallback, but not used by the macOS launcher
- CLI: batch-friendly export path

## Run

From the project root:

```bash
python3 -m pip install -r requirements.txt
python3 run_web.py
```

On macOS, you can also double-click:

```text
Launch SpriteSheet Maker.command
```

The launcher starts a local server at `http://127.0.0.1:8765` and opens it in your browser. Keep the Terminal window open while using the tool.

In the Web UI, `Save Folder` can be a relative project path such as `assets/output` or an absolute macOS path. The `Choose` button opens a native macOS folder picker.

If the browser keeps an older interface after an update, refresh the page. Static files are versioned and served with no-cache headers, but an already-open tab can still need one manual refresh.

CLI example:

```bash
PYTHONPATH=src python3 run_cli.py examples/sample_vfx.gif \
  --output assets/output/sample_sheet.png \
  --black-threshold 20 \
  --soft-edge 8 \
  --columns 4 \
  --padding 2
```

`--padding` is kept for CLI compatibility, but it means transparent margin around each frame canvas. For example, `--padding 20` adds 20 px of transparent space on all four sides of every frame, affects exported individual frames, and does not insert gaps between cells in the final sheet.

Video input uses `imageio-ffmpeg`, which bundles ffmpeg for most machines. If video decoding still fails, install system ffmpeg:

```bash
brew install ffmpeg
```

## Optional App Bundle

To build a macOS `.app` bundle, install PyInstaller and run:

```bash
bash scripts/build_mac_app.sh
```

The generated app will be in `dist/`.

To build a Windows `.exe`, run this on a Windows PC:

```bat
scripts\build_windows_exe.bat
```

The generated executable will be `dist\SpriteSheet Maker.exe`.

Or let GitHub Actions build it for you on Windows:

1. Push this repository to GitHub.
2. Open `Actions` -> `Build Windows EXE`.
3. Click `Run workflow`, or push a code change to `main`/`master`.
4. Download the `SpriteSheet-Maker-Windows` artifact from the completed run.

## Project Structure

```text
assets/
  input/      # user-provided source media, keep large/raw files out of Git when needed
  output/     # generated sprite sheets and metadata
  previews/   # preview screenshots and QA images
  temp/       # temporary working files
examples/    # small reproducible examples
src/unity_vx_motion_master/
  cli.py
  config.py
  frame_source.py
  gui.py
  processor.py
  web_app.py
  web_static/
tests/
handoff.md
Launch SpriteSheet Maker.command
```

## GitHub Notes

Generated media can get large. Before publishing, add any bulky `assets/input/*` or generated `assets/output/*` files to `.gitignore` unless they are small examples.
