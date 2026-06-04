#!/bin/bash
cd "$(dirname "$0")"
python3 - <<'PY' >/dev/null 2>&1 || python3 -m pip install -r requirements.txt
import PIL
import imageio_ffmpeg
PY
python3 run_web.py
