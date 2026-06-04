from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Tuple


Anchor = Literal["center", "top", "bottom"]
BackgroundMode = Literal["checker", "transparent", "black", "white", "gray"]


@dataclass(frozen=True)
class ProcessSettings:
    input_path: Path
    output_path: Path
    fps: Optional[float] = None
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    remove_black: bool = True
    black_threshold: int = 20
    soft_edge: int = 8
    alpha_strength: float = 1.0
    auto_size: bool = True
    frame_size: Optional[Tuple[int, int]] = None
    anchor: Anchor = "center"
    columns: Optional[int] = None
    padding: int = 0
    max_texture_size: Optional[int] = 4096
    export_frames: bool = False
    export_metadata: bool = True


@dataclass(frozen=True)
class SheetMetadata:
    frame_count: int
    frame_width: int
    frame_height: int
    columns: int
    rows: int
    padding: int
    sheet_width: int
    sheet_height: int
    source_width: int
    source_height: int
    crop_box: Tuple[int, int, int, int]
    anchor: Anchor
    scale: float
