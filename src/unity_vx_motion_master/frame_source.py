from __future__ import annotations

import subprocess
import tempfile
import re
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image, ImageSequence


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".gif", ".webm", ".avi", ".png", ".jpg", ".jpeg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi"}


class FrameSourceError(RuntimeError):
    pass


def load_frames(path: Path, fps: Optional[float] = None) -> list[Image.Image]:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise FrameSourceError(f"Unsupported input type: {suffix}")
    if suffix == ".gif":
        return _load_gif(path, fps=fps)
    if suffix in {".png", ".jpg", ".jpeg"}:
        return [Image.open(path).convert("RGBA")]
    return _load_video_with_ffmpeg(path, fps=fps)


def select_frame_range(
    frames: list[Image.Image],
    start_frame: Optional[int],
    end_frame: Optional[int],
) -> list[Image.Image]:
    if not frames:
        return []
    start = 0 if start_frame is None else max(0, start_frame)
    end = len(frames) - 1 if end_frame is None else min(len(frames) - 1, end_frame)
    if end < start:
        raise FrameSourceError("End frame must be greater than or equal to start frame.")
    return frames[start : end + 1]


def estimate_source_duration_seconds(path: Path) -> Optional[float]:
    suffix = path.suffix.lower()
    if suffix == ".gif":
        return _estimate_gif_duration_seconds(path)
    if suffix in VIDEO_EXTENSIONS:
        return _estimate_video_duration_seconds(path)
    return None


def _load_gif(path: Path, fps: Optional[float] = None) -> list[Image.Image]:
    image = Image.open(path)
    frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(image)]
    if fps is None or fps <= 0:
        return frames

    durations = [max(1, frame.info.get("duration", image.info.get("duration", 100))) for frame in ImageSequence.Iterator(image)]
    return _resample_frames_by_timeline(frames, durations, fps)


def _estimate_gif_duration_seconds(path: Path) -> Optional[float]:
    image = Image.open(path)
    durations = [max(1, frame.info.get("duration", image.info.get("duration", 100))) for frame in ImageSequence.Iterator(image)]
    total_ms = sum(durations)
    return total_ms / 1000.0 if total_ms > 0 else None


def _resample_frames_by_timeline(frames: list[Image.Image], durations_ms: list[int], fps: float) -> list[Image.Image]:
    if not frames:
        return []
    total_ms = sum(durations_ms)
    if total_ms <= 0:
        return frames

    step_ms = 1000.0 / fps
    timeline = []
    cursor = 0
    for index, duration in enumerate(durations_ms):
        timeline.append((cursor, cursor + duration, index))
        cursor += duration

    sampled = []
    t = 0.0
    while t < total_ms:
        for start, end, index in timeline:
            if start <= t < end:
                sampled.append(frames[index].copy())
                break
        t += step_ms
    return sampled or [frames[0].copy()]


def _load_video_with_ffmpeg(path: Path, fps: Optional[float] = None) -> list[Image.Image]:
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise FrameSourceError(
            "Video input requires ffmpeg. Install ffmpeg, or use GIF/PNG input for now."
        )

    with tempfile.TemporaryDirectory(prefix="uvxmm_frames_") as tmp:
        tmpdir = Path(tmp)
        pattern = tmpdir / "frame_%06d.png"
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(path)]
        if fps and fps > 0:
            command.extend(["-vf", f"fps={fps}"])
        command.extend([str(pattern)])
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise FrameSourceError(result.stderr.strip() or "ffmpeg failed to decode the video.")
        return [Image.open(frame).convert("RGBA") for frame in sorted(tmpdir.glob("frame_*.png"))]


def _estimate_video_duration_seconds(path: Path) -> Optional[float]:
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        return None
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _find_ffmpeg() -> Optional[str]:
    try:
        import imageio_ffmpeg

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled:
            return bundled
    except Exception:
        pass

    for candidate in ("ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        try:
            result = subprocess.run([candidate, "-version"], capture_output=True, text=True)
        except FileNotFoundError:
            continue
        if result.returncode == 0:
            return candidate
    return None
