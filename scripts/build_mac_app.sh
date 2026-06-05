#!/bin/bash
set -e
cd "$(dirname "$0")/.."
export PYINSTALLER_CONFIG_DIR="${TMPDIR:-/tmp}/spritesheet-maker-pyinstaller"
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller \
  --name "SpriteSheet Maker" \
  --windowed \
  --clean \
  --noconfirm \
  --paths "src" \
  --add-data "assets:assets" \
  --add-data "src/unity_vx_motion_master/web_static:src/unity_vx_motion_master/web_static" \
  --collect-binaries imageio_ffmpeg \
  run_web.py
