from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw

from .config import ProcessSettings, SheetMetadata
from .frame_source import FrameSourceError, load_frames, select_frame_range


RGBA = tuple[int, int, int, int]


class ProcessingError(RuntimeError):
    pass


def process_to_sheet(settings: ProcessSettings) -> SheetMetadata:
    frames = load_frames(settings.input_path, fps=settings.fps)
    frames = select_frame_range(frames, settings.start_frame, settings.end_frame)
    if not frames:
        raise ProcessingError("No frames were loaded from the input.")

    processed = [
        remove_black_background(frame, settings.black_threshold, settings.soft_edge, settings.alpha_strength)
        if settings.remove_black
        else frame.convert("RGBA")
        for frame in frames
    ]
    source_width, source_height = processed[0].size
    crop_box = find_union_alpha_bbox(processed)
    cropped = [frame.crop(crop_box) for frame in processed]
    canvas_size = resolve_canvas_size(crop_box, settings)
    normalized = [add_canvas_margin(place_on_canvas(frame, canvas_size, settings.anchor), settings.padding) for frame in cropped]
    normalized, scale = fit_frames_to_texture(normalized, settings)
    sheet, columns, rows = compose_sheet(normalized, settings.columns)

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
        padding=settings.padding,
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
    return metadata


def remove_black_background(
    image: Image.Image,
    black_threshold: int = 20,
    soft_edge: int = 8,
    alpha_strength: float = 1.0,
) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size
    threshold = max(0, min(255, int(black_threshold)))
    feather = max(0, int(soft_edge))
    alpha_strength = max(0.0, min(4.0, float(alpha_strength)))
    fade_end = min(255, threshold + feather)

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            brightness = max(r, g, b)
            if brightness <= threshold:
                next_alpha = 0
            elif feather > 0 and brightness < fade_end:
                t = (brightness - threshold) / max(1, feather)
                next_alpha = int(a * max(0.0, min(1.0, t * alpha_strength)))
            else:
                next_alpha = int(a * alpha_strength)
            pixels[x, y] = (r, g, b, max(0, min(255, next_alpha)))
    return image


def find_union_alpha_bbox(frames: Iterable[Image.Image]) -> Tuple[int, int, int, int]:
    union: Optional[Image.Image] = None
    width = height = 0
    for frame in frames:
        alpha = frame.convert("RGBA").getchannel("A")
        width, height = frame.size
        union = alpha if union is None else ImageChops.lighter(union, alpha)
    if union is None:
        raise ProcessingError("No frames were supplied for crop analysis.")
    bbox = union.getbbox()
    if bbox is None:
        return (0, 0, width, height)
    return bbox


def resolve_canvas_size(crop_box: Tuple[int, int, int, int], settings: ProcessSettings) -> Tuple[int, int]:
    crop_width = max(1, crop_box[2] - crop_box[0])
    crop_height = max(1, crop_box[3] - crop_box[1])
    if settings.auto_size or not settings.frame_size:
        return even_size((crop_width, crop_height))
    width, height = settings.frame_size
    return even_size((max(crop_width, int(width)), max(crop_height, int(height))))


def place_on_canvas(frame: Image.Image, canvas_size: Tuple[int, int], anchor: str = "center") -> Image.Image:
    canvas_width, canvas_height = canvas_size
    if frame.width > canvas_width or frame.height > canvas_height:
        scale = min(canvas_width / frame.width, canvas_height / frame.height)
        next_size = (max(1, int(frame.width * scale)), max(1, int(frame.height * scale)))
        frame = frame.resize(next_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    x = (canvas_width - frame.width) // 2
    if anchor == "top":
        y = 0
    elif anchor == "bottom":
        y = canvas_height - frame.height
    else:
        y = (canvas_height - frame.height) // 2
    canvas.alpha_composite(frame, (x, y))
    return canvas


def even_size(size: Tuple[int, int]) -> Tuple[int, int]:
    width, height = size
    width = max(2, int(width))
    height = max(2, int(height))
    return width + (width % 2), height + (height % 2)


def ensure_even_canvas(image: Image.Image) -> Image.Image:
    next_size = even_size(image.size)
    if next_size == image.size:
        return image
    canvas = Image.new("RGBA", next_size, (0, 0, 0, 0))
    x = (next_size[0] - image.width) // 2
    y = (next_size[1] - image.height) // 2
    canvas.alpha_composite(image.convert("RGBA"), (x, y))
    return canvas


def add_canvas_margin(image: Image.Image, margin: int = 0) -> Image.Image:
    margin = max(0, int(margin))
    if margin <= 0:
        return ensure_even_canvas(image)
    image = image.convert("RGBA")
    canvas = Image.new("RGBA", (image.width + margin * 2, image.height + margin * 2), (0, 0, 0, 0))
    canvas.alpha_composite(image, (margin, margin))
    return ensure_even_canvas(canvas)


def fit_frames_to_texture(frames: list[Image.Image], settings: ProcessSettings) -> tuple[list[Image.Image], float]:
    if not frames or not settings.max_texture_size:
        return frames, 1.0
    sheet_width, sheet_height, columns, rows = estimate_sheet_size(
        len(frames),
        frames[0].width,
        frames[0].height,
        settings.columns,
    )
    max_size = settings.max_texture_size
    if sheet_width <= max_size and sheet_height <= max_size:
        return frames, 1.0

    scale = min(max_size / sheet_width, max_size / sheet_height)
    scale = max(0.01, min(1.0, scale))
    resized = []
    for frame in frames:
        next_size = (max(1, int(frame.width * scale)), max(1, int(frame.height * scale)))
        resized.append(ensure_even_canvas(frame.resize(next_size, Image.Resampling.LANCZOS)))
    return resized, scale


def compose_sheet(
    frames: list[Image.Image],
    columns: Optional[int] = None,
    rows: Optional[int] = None,
) -> tuple[Image.Image, int, int]:
    if not frames:
        raise ProcessingError("No frames to compose.")
    frame_width, frame_height = frames[0].size
    columns = resolve_columns(len(frames), columns)
    rows = max(1, int(rows)) if rows and rows > 0 else math.ceil(len(frames) / columns)
    sheet_width = columns * frame_width
    sheet_height = rows * frame_height
    sheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        if index >= columns * rows:
            break
        col = index % columns
        row = index // columns
        x = col * frame_width
        y = row * frame_height
        sheet.alpha_composite(frame, (x, y))
    return ensure_even_canvas(sheet), columns, rows


def resolve_columns(frame_count: int, columns: Optional[int]) -> int:
    if columns and columns > 0:
        return min(frame_count, columns)
    return max(1, math.ceil(math.sqrt(frame_count)))


def estimate_sheet_size(
    frame_count: int,
    frame_width: int,
    frame_height: int,
    columns: Optional[int],
) -> tuple[int, int, int, int]:
    cols = resolve_columns(frame_count, columns)
    rows = math.ceil(frame_count / cols)
    width = cols * frame_width
    height = rows * frame_height
    return width, height, cols, rows


def checkerboard(size: Tuple[int, int], tile: int = 16) -> Image.Image:
    image = Image.new("RGBA", size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    colors = ((230, 232, 235, 255), (184, 189, 197, 255))
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            color = colors[((x // tile) + (y // tile)) % 2]
            draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=color)
    return image


def preview_composite(image: Image.Image, mode: str = "checker") -> Image.Image:
    image = image.convert("RGBA")
    if mode == "transparent":
        return image
    backgrounds: dict[str, RGBA] = {
        "black": (0, 0, 0, 255),
        "white": (255, 255, 255, 255),
        "gray": (128, 128, 128, 255),
    }
    background = checkerboard(image.size) if mode == "checker" else Image.new("RGBA", image.size, backgrounds.get(mode, backgrounds["gray"]))
    background.alpha_composite(image)
    return background
