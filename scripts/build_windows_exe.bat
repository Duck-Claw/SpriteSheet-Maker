@echo off
setlocal
cd /d "%~dp0\.."
py -3 -m pip install -r requirements.txt pyinstaller
py -3 -m PyInstaller ^
  --name "SpriteSheet Maker" ^
  --onefile ^
  --noconsole ^
  --clean ^
  --paths "src" ^
  --add-data "assets;assets" ^
  --add-data "src\unity_vx_motion_master\web_static;src\unity_vx_motion_master\web_static" ^
  --collect-binaries imageio_ffmpeg ^
  run_web.py
echo.
echo Built dist\SpriteSheet Maker.exe
