from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image

from unity_vx_motion_master.config import ProcessSettings
from unity_vx_motion_master.processor import process_to_sheet


def main() -> None:
    source = Path("examples/sample_vfx.gif")
    if not source.exists():
        raise SystemExit("Run examples/make_sample_gif.py first.")
    output = Path("assets/output/smoke_sheet.png")
    metadata = process_to_sheet(
        ProcessSettings(
            input_path=source,
            output_path=output,
            columns=4,
            padding=2,
            export_frames=True,
        )
    )
    image = Image.open(output)
    assert image.mode == "RGBA"
    assert metadata.frame_count == 16
    assert metadata.columns == 4
    assert metadata.frame_width % 2 == 0
    assert metadata.frame_height % 2 == 0
    assert metadata.sheet_width % 2 == 0
    assert metadata.sheet_height % 2 == 0
    assert metadata.sheet_width == image.width
    assert metadata.sheet_height == image.height
    print(f"OK: {output} {image.width}x{image.height}")


if __name__ == "__main__":
    main()
