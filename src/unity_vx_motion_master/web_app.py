from __future__ import annotations

import base64
import io
import json
import mimetypes
import platform
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

from .config import ProcessSettings, SheetMetadata
from .frame_source import estimate_source_duration_seconds, load_frames, select_frame_range
from .processor import (
    compose_sheet,
    ensure_even_canvas,
    even_size,
    find_union_alpha_bbox,
    place_on_canvas,
    preview_composite,
    remove_black_background,
    resolve_canvas_size,
)


APP_NAME = "SpriteSheet Maker"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_ROOT
INPUT_DIR = APP_ROOT / "assets" / "input"
OUTPUT_DIR = APP_ROOT / "assets" / "output"
STATIC_DIR = BUNDLE_ROOT / "src" / "unity_vx_motion_master" / "web_static"
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


class WebAppError(RuntimeError):
    pass


class MotionMasterHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_file(STATIC_DIR / "index.html", "text/html")
            return
        if parsed.path == "/api/job":
            query = dict(item.split("=", 1) for item in parsed.query.split("&") if "=" in item)
            self._handle_job_status(query.get("id", ""))
            return
        if parsed.path == "/api/download":
            query = dict(item.split("=", 1) for item in parsed.query.split("&") if "=" in item)
            self._handle_download(query.get("id", ""))
            return
        if parsed.path.startswith("/static/"):
            requested = STATIC_DIR / unquote(parsed.path.removeprefix("/static/"))
            self._serve_file(requested)
            return
        if parsed.path.startswith("/assets/output/"):
            requested = OUTPUT_DIR / unquote(parsed.path.removeprefix("/assets/output/"))
            self._serve_file(requested)
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/upload":
                self._handle_upload()
            elif self.path == "/api/choose-output-dir":
                self._handle_choose_output_dir()
            elif self.path == "/api/preview":
                self._start_job("preview")
            elif self.path == "/api/export":
                self._start_job("export")
            else:
                self._send_json({"error": "Not found"}, status=404)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web] {self.address_string()} {format % args}")

    def _handle_upload(self) -> None:
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename, data = self._read_multipart_file("file")
        if not filename:
            raise WebAppError("No file uploaded.")
        filename = _safe_filename(filename)
        target = INPUT_DIR / filename
        target.write_bytes(data)
        self._send_json({"path": str(target), "filename": filename})

    def _read_multipart_file(self, field_name: str) -> tuple[str, bytes]:
        content_type = self.headers.get("Content-Type", "")
        boundary = _multipart_boundary(content_type)
        if not boundary:
            raise WebAppError("Upload request is missing a multipart boundary.")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            raise WebAppError("Upload request is empty.")
        return _extract_multipart_file(self.rfile.read(length), boundary, field_name)

    def _handle_choose_output_dir(self) -> None:
        if platform.system() != "Darwin":
            output_dir = _choose_output_dir_with_tk()
            if not output_dir:
                raise WebAppError("Folder selection was cancelled.")
            self._send_json({"outputDir": output_dir})
            return
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'set theFolder to choose folder with prompt "Choose a folder for exported sprite sheets"',
                "-e",
                "POSIX path of theFolder",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise WebAppError(result.stderr.strip() or "Folder selection was cancelled.")
        self._send_json({"outputDir": result.stdout.strip()})

    def _start_job(self, kind: str) -> None:
        payload = self._read_json()
        settings = _settings_from_payload(payload, for_preview=kind == "preview")
        job_id = uuid.uuid4().hex
        _set_job(job_id, {"state": "running", "progress": 0, "message": "Queued...", "kind": kind})
        worker = threading.Thread(target=_run_job, args=(job_id, kind, payload, settings), daemon=True)
        worker.start()
        self._send_json({"jobId": job_id, "state": "running", "progress": 0}, status=202)

    def _handle_job_status(self, job_id: str) -> None:
        with JOBS_LOCK:
            job = JOBS.get(job_id)
        if not job:
            self._send_json({"error": "Job not found"}, status=404)
            return
        self._send_json(job)

    def _handle_download(self, job_id: str) -> None:
        with JOBS_LOCK:
            job = JOBS.get(job_id)
        if not job or job.get("state") != "done" or not job.get("outputPath"):
            self._send_json({"error": "Download is not ready"}, status=404)
            return
        path = Path(job["outputPath"])
        if not path.exists():
            self._send_json({"error": "Output file no longer exists"}, status=404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _serve_file(self, path: Path, content_type: str | None = None) -> None:
        path = path.resolve()
        allowed_roots = [STATIC_DIR.resolve(), OUTPUT_DIR.resolve()]
        if not any(str(path).startswith(str(root)) for root in allowed_roots):
            self._send_json({"error": "Forbidden"}, status=403)
            return
        if not path.exists() or not path.is_file():
            self._send_json({"error": "Not found"}, status=404)
            return
        content_type = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _settings_from_payload(payload: dict, for_preview: bool) -> ProcessSettings:
    input_path = Path(payload.get("inputPath", ""))
    if not input_path.exists():
        raise WebAppError("Input file does not exist. Upload a file first.")

    output_name = _safe_filename(payload.get("outputName") or f"{input_path.stem}_sheet.png")
    if not output_name.lower().endswith(".png"):
        output_name += ".png"
    output_dir_raw = str(payload.get("outputDir") or "").strip()
    output_dir = Path(output_dir_raw).expanduser() if output_dir_raw else OUTPUT_DIR
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_path = output_dir / output_name

    auto_size = bool(payload.get("autoSize", True))
    frame_size = None
    if not auto_size:
        frame_size = (_int(payload.get("frameWidth"), 256), _int(payload.get("frameHeight"), 256))

    return ProcessSettings(
        input_path=input_path,
        output_path=output_path,
        fps=_float_or_none(payload.get("fps")),
        start_frame=_int_or_none(payload.get("startFrame")),
        end_frame=_int_or_none(payload.get("endFrame")),
        remove_black=bool(payload.get("removeBlack", True)),
        black_threshold=_int(payload.get("blackThreshold"), 20),
        soft_edge=_int(payload.get("softEdge"), 8),
        alpha_strength=_float(payload.get("alphaStrength"), 1.0),
        auto_size=auto_size,
        frame_size=frame_size,
        anchor=payload.get("anchor", "center"),
        columns=_int_or_none(payload.get("columns")),
        padding=_int(payload.get("padding"), 0),
        max_texture_size=_int_or_none(payload.get("maxTextureSize")),
        export_frames=bool(payload.get("exportFrames", False)) and not for_preview,
    )


def _run_job(job_id: str, kind: str, payload: dict, settings: ProcessSettings) -> None:
    try:
        result = _build_sheet_result(job_id, kind, payload, settings)
        _set_job(job_id, {"state": "done", "progress": 100, "message": "Done.", **result})
    except Exception as exc:
        _set_job(job_id, {"state": "error", "progress": 100, "message": str(exc), "error": str(exc)})


def _build_sheet_result(job_id: str, kind: str, payload: dict, settings: ProcessSettings) -> dict:
    layout_mode = payload.get("layoutMode", "fpsAuto")
    grid_priority = bool(payload.get("gridPriority", False))
    tight_grid = bool(payload.get("tightGrid", False))
    grid_rows = _int_or_none(payload.get("rows"))
    grid_columns = _int_or_none(payload.get("columns"))
    target_grid_count = grid_rows * grid_columns if (grid_priority or tight_grid) and grid_rows and grid_columns else None
    decode_fps = None if target_grid_count else settings.fps
    effective_padding = 0 if tight_grid else settings.padding

    _set_job(job_id, {"progress": 5, "message": "Decoding source frames..."})
    source_duration = estimate_source_duration_seconds(settings.input_path)
    frames = load_frames(settings.input_path, fps=decode_fps)
    loaded_frame_count = len(frames)
    frames = select_frame_range(frames, settings.start_frame, settings.end_frame)
    if not frames:
        raise WebAppError("No frames loaded.")
    selected_duration = _estimate_selected_duration_seconds(source_duration, loaded_frame_count, settings.start_frame, settings.end_frame)
    actual_output_frame_count = target_grid_count or len(frames)
    effective_fps = _calculate_effective_fps(actual_output_frame_count, selected_duration, None if target_grid_count else settings.fps)
    if target_grid_count:
        _set_job(job_id, {"progress": 8, "message": f"Sampling {target_grid_count} frames for filled grid..."})
        frames = _sample_evenly(frames, target_grid_count)
    if kind == "preview" and len(frames) > 80:
        stride = max(1, len(frames) // 80)
        frames = frames[::stride]

    processed = []
    total = len(frames)
    for index, frame in enumerate(frames):
        if settings.remove_black:
            processed.append(remove_black_background(frame, settings.black_threshold, settings.soft_edge, settings.alpha_strength))
        else:
            processed.append(frame.convert("RGBA"))
        progress = 10 + int(((index + 1) / total) * 45)
        _set_job(job_id, {"progress": progress, "message": f"Removing background {index + 1}/{total}..."})

    _set_job(job_id, {"progress": 62, "message": "Finding unified crop bounds..."})
    source_width, source_height = processed[0].size
    crop_box = find_union_alpha_bbox(processed)
    canvas_size = _resolve_canvas_size_for_job(crop_box, settings, payload)
    if tight_grid:
        _set_job(job_id, {"progress": 63, "message": f"Tight grid cell size: {canvas_size[0]}x{canvas_size[1]}..."})
    elif grid_priority:
        _set_job(job_id, {"progress": 63, "message": f"Rows/columns priority cell size: {canvas_size[0]}x{canvas_size[1]}..."})

    normalized = []
    for index, frame in enumerate(processed):
        normalized.append(place_on_canvas(frame.crop(crop_box), canvas_size, settings.anchor))
        progress = 64 + int(((index + 1) / total) * 16)
        _set_job(job_id, {"progress": progress, "message": f"Normalizing frame canvas {index + 1}/{total}..."})

    scale = 1.0

    _set_job(job_id, {"progress": 88, "message": "Composing sprite sheet..."})
    sheet_columns = _resolve_layout_columns(payload, normalized)
    sheet_rows = grid_rows if layout_mode == "customGrid" and grid_rows and grid_columns else None
    sheet, columns, rows = compose_sheet(normalized, sheet_columns, sheet_rows, effective_padding)
    if kind == "export" and settings.max_texture_size and (sheet.width > settings.max_texture_size or sheet.height > settings.max_texture_size):
        _set_job(job_id, {"progress": 91, "message": "Scaling to max texture size..."})
        target_cell = _fit_even_cell_size(settings.max_texture_size, columns, rows, effective_padding)
        scale = min(target_cell[0] / normalized[0].width, target_cell[1] / normalized[0].height)
        scale = max(0.01, min(1.0, scale))
        normalized = [
            ensure_even_canvas(frame.resize((max(1, int(frame.width * scale)), max(1, int(frame.height * scale))), Image.Resampling.LANCZOS))
            for frame in normalized
        ]
        sheet, columns, rows = compose_sheet(normalized, sheet_columns, sheet_rows, effective_padding)

    output_path = None
    metadata = None
    if kind == "export":
        _set_job(job_id, {"progress": 93, "message": "Saving PNG and metadata..."})
        settings.output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(settings.output_path)
        if settings.export_frames:
            export_dir = settings.output_path.with_suffix("").parent / f"{settings.output_path.stem}_frames"
            export_dir.mkdir(parents=True, exist_ok=True)
            for index, frame in enumerate(normalized):
                frame.save(export_dir / f"frame_{index:04d}.png")
        metadata = SheetMetadata(
            frame_count=len(normalized),
            frame_width=normalized[0].width,
            frame_height=normalized[0].height,
            columns=columns,
            rows=rows,
            padding=effective_padding,
            sheet_width=sheet.width,
            sheet_height=sheet.height,
            source_width=source_width,
            source_height=source_height,
            crop_box=crop_box,
            anchor=settings.anchor,
            scale=scale,
        )
        if settings.export_metadata:
            settings.output_path.with_suffix(".json").write_text(json.dumps(metadata.__dict__, indent=2), encoding="utf-8")
        output_path = str(settings.output_path)

    preview = preview_composite(sheet, payload.get("background", "checker"))
    preview.thumbnail((1200, 860), Image.Resampling.LANCZOS)
    return {
        "image": _image_to_data_url(preview),
        "frameCount": len(normalized),
        "frameWidth": normalized[0].width,
        "frameHeight": normalized[0].height,
        "columns": columns,
        "rows": rows,
        "effectiveFps": effective_fps,
        "cropBox": crop_box,
        "outputPath": output_path,
        "metadata": metadata.__dict__ if metadata else None,
    }


def _set_job(job_id: str, patch: dict) -> None:
    with JOBS_LOCK:
        current = JOBS.get(job_id, {})
        current.update(patch)
        JOBS[job_id] = current


def _sample_evenly(frames: list[Image.Image], count: int) -> list[Image.Image]:
    count = max(1, int(count))
    if len(frames) == 1:
        return [frames[0].copy() for _ in range(count)]
    if count == 1:
        return [frames[0].copy()]
    max_index = len(frames) - 1
    sampled = []
    for index in range(count):
        source_index = round(index * max_index / (count - 1))
        sampled.append(frames[source_index].copy())
    return sampled


def _estimate_selected_duration_seconds(
    source_duration: Optional[float],
    loaded_frame_count: int,
    start_frame: Optional[int],
    end_frame: Optional[int],
) -> Optional[float]:
    if not source_duration or source_duration <= 0 or loaded_frame_count <= 0:
        return None
    start = 0 if start_frame is None else max(0, start_frame)
    end = loaded_frame_count - 1 if end_frame is None else min(loaded_frame_count - 1, end_frame)
    if end < start:
        return None
    selected_count = end - start + 1
    return source_duration * selected_count / loaded_frame_count


def _calculate_effective_fps(
    frame_count: int,
    selected_duration: Optional[float],
    fallback_fps: Optional[float],
) -> Optional[float]:
    if selected_duration and selected_duration > 0:
        return round(frame_count / selected_duration, 2)
    if fallback_fps and fallback_fps > 0:
        return round(fallback_fps, 2)
    return None


def _choose_output_dir_with_tk() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:
        raise WebAppError("Folder picker is unavailable. Type an output folder path instead.") from exc

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return filedialog.askdirectory(title="Choose a folder for exported sprite sheets") or ""
    finally:
        root.destroy()


def _resolve_canvas_size_for_job(crop_box: tuple[int, int, int, int], settings: ProcessSettings, payload: dict) -> tuple[int, int]:
    if payload.get("layoutMode", "fpsAuto") == "customGrid" and bool(payload.get("tightGrid", False)):
        return even_size((max(1, crop_box[2] - crop_box[0]), max(1, crop_box[3] - crop_box[1])))
    if (
        payload.get("layoutMode", "fpsAuto") == "customGrid"
        and bool(payload.get("gridPriority", False))
        and _int_or_none(payload.get("rows"))
        and _int_or_none(payload.get("columns"))
        and settings.max_texture_size
    ):
        rows = _int(payload.get("rows"), 1)
        columns = _int(payload.get("columns"), 1)
        padding = _int(payload.get("padding"), 0)
        return _fit_even_cell_size(settings.max_texture_size, columns, rows, padding)
    return resolve_canvas_size(crop_box, settings)


def _fit_even_cell_size(max_texture: int, columns: int, rows: int, padding: int) -> tuple[int, int]:
    gap_width = max(0, columns - 1) * padding
    gap_height = max(0, rows - 1) * padding
    available_width = max_texture - gap_width
    available_height = max_texture - gap_height
    if available_width < columns or available_height < rows:
        raise WebAppError("Rows, columns, and padding do not fit inside Max Texture.")

    cell_width = _even_floor(available_width // columns)
    cell_height = _even_floor(available_height // rows)
    if cell_width < 2 or cell_height < 2:
        raise WebAppError("Rows/columns priority produced a cell smaller than 2px.")

    while _even_sheet_extent(columns, cell_width, padding) > max_texture and cell_width > 2:
        cell_width -= 2
    while _even_sheet_extent(rows, cell_height, padding) > max_texture and cell_height > 2:
        cell_height -= 2

    if _even_sheet_extent(columns, cell_width, padding) > max_texture or _even_sheet_extent(rows, cell_height, padding) > max_texture:
        raise WebAppError("Could not fit an even cell size inside Max Texture.")
    return even_size((cell_width, cell_height))


def _even_floor(value: int) -> int:
    value = max(1, int(value))
    return value if value % 2 == 0 else value - 1


def _even_sheet_extent(count: int, cell_size: int, padding: int) -> int:
    extent = count * cell_size + max(0, count - 1) * padding
    return extent + (extent % 2)


def _resolve_layout_columns(payload: dict, frames: list[Image.Image]) -> Optional[int]:
    layout_mode = payload.get("layoutMode", "fpsAuto")
    columns = _int_or_none(payload.get("columns"))
    rows = _int_or_none(payload.get("rows"))
    if layout_mode == "customGrid" and columns:
        return columns
    if columns:
        return columns
    if not frames:
        return None

    max_texture = _int_or_none(payload.get("maxTextureSize")) or 4096
    padding = _int(payload.get("padding"), 0)
    frame_width = frames[0].width
    cell_width = frame_width + padding
    if cell_width <= 0:
        return None
    texture_fit_columns = max(1, (max_texture + padding) // cell_width)
    return min(len(frames), texture_fit_columns)


def _safe_filename(name: str) -> str:
    cleaned = "".join(char for char in Path(name).name if char.isalnum() or char in "._- ")
    return cleaned.strip() or f"upload_{int(time.time())}.dat"


def _multipart_boundary(content_type: str) -> str:
    media_type, *params = content_type.split(";")
    if media_type.strip().lower() != "multipart/form-data":
        return ""
    for param in params:
        key, separator, value = param.strip().partition("=")
        if separator and key.lower() == "boundary":
            return value.strip().strip('"')
    return ""


def _extract_multipart_file(body: bytes, boundary: str, field_name: str) -> tuple[str, bytes]:
    delimiter = f"--{boundary}".encode("utf-8")
    for part in body.split(delimiter):
        if not part or part in (b"--", b"--\r\n"):
            continue
        if part.startswith(b"\r\n"):
            part = part[2:]
        if part.endswith(b"--"):
            part = part[:-2]
        if part.endswith(b"\r\n"):
            part = part[:-2]

        header_blob, separator, data = part.partition(b"\r\n\r\n")
        if not separator:
            continue
        headers = _parse_multipart_headers(header_blob)
        disposition = headers.get("content-disposition", "")
        disposition_type, params = _parse_header_value(disposition)
        if disposition_type != "form-data":
            continue
        if params.get("name") == field_name and params.get("filename"):
            return params["filename"], data
    raise WebAppError("No file uploaded.")


def _parse_multipart_headers(header_blob: bytes) -> dict[str, str]:
    headers = {}
    for raw_line in header_blob.decode("iso-8859-1").split("\r\n"):
        key, separator, value = raw_line.partition(":")
        if separator:
            headers[key.strip().lower()] = value.strip()
    return headers


def _parse_header_value(value: str) -> tuple[str, dict[str, str]]:
    parts = [part.strip() for part in value.split(";") if part.strip()]
    if not parts:
        return "", {}
    params = {}
    for part in parts[1:]:
        key, separator, raw_value = part.partition("=")
        if separator:
            params[key.strip().lower()] = raw_value.strip().strip('"')
    return parts[0].lower(), params


def _image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _int_or_none(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _int(value: object, default: int) -> int:
    if value in (None, ""):
        return default
    return int(value)


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _float(value: object, default: float) -> float:
    if value in (None, ""):
        return default
    return float(value)


def main(port: int = 8765, open_browser: bool = True) -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), MotionMasterHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"{APP_NAME} running at {url}")
    print("Keep this terminal open while using the tool.")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
