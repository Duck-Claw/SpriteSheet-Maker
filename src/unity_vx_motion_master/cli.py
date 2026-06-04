from __future__ import annotations

import argparse
from pathlib import Path

from .config import ProcessSettings
from .processor import process_to_sheet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spritesheet-maker", description="Build transparent sprite sheets from GIF/video/VFX frames.")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("assets/output/sprite_sheet.png"))
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument("--start-frame", type=int, default=None)
    parser.add_argument("--end-frame", type=int, default=None)
    parser.add_argument("--black-threshold", type=int, default=20)
    parser.add_argument("--soft-edge", type=int, default=8)
    parser.add_argument("--alpha-strength", type=float, default=1.0)
    parser.add_argument("--keep-black", action="store_true")
    parser.add_argument("--frame-width", type=int, default=None)
    parser.add_argument("--frame-height", type=int, default=None)
    parser.add_argument("--anchor", choices=("center", "top", "bottom"), default="center")
    parser.add_argument("--columns", type=int, default=None)
    parser.add_argument("--padding", type=int, default=0)
    parser.add_argument("--max-texture-size", type=int, default=4096)
    parser.add_argument("--export-frames", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    frame_size = None
    auto_size = True
    if args.frame_width and args.frame_height:
        frame_size = (args.frame_width, args.frame_height)
        auto_size = False

    settings = ProcessSettings(
        input_path=args.input,
        output_path=args.output,
        fps=args.fps,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        remove_black=not args.keep_black,
        black_threshold=args.black_threshold,
        soft_edge=args.soft_edge,
        alpha_strength=args.alpha_strength,
        auto_size=auto_size,
        frame_size=frame_size,
        anchor=args.anchor,
        columns=args.columns,
        padding=args.padding,
        max_texture_size=args.max_texture_size,
        export_frames=args.export_frames,
    )
    metadata = process_to_sheet(settings)
    print(f"Saved {settings.output_path}")
    print(f"{metadata.frame_count} frames, {metadata.frame_width}x{metadata.frame_height}, sheet {metadata.sheet_width}x{metadata.sheet_height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
