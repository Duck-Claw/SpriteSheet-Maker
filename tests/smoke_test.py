from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image

from unity_vx_motion_master.config import ProcessSettings
from unity_vx_motion_master.processor import process_to_sheet
from unity_vx_motion_master.web_app import _extract_multipart_file, _multipart_boundary


def main() -> None:
    _assert_multipart_upload_parser()
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


def _assert_multipart_upload_parser() -> None:
    boundary = "----SpriteSheetMakerTest"
    content_type = f'multipart/form-data; boundary="{boundary}"'
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="sample.gif"\r\n'
        "Content-Type: image/gif\r\n"
        "\r\n"
    ).encode("utf-8") + b"GIF89a-test-bytes\r\n" + f"--{boundary}--\r\n".encode("utf-8")
    assert _multipart_boundary(content_type) == boundary
    filename, data = _extract_multipart_file(body, boundary, "file")
    assert filename == "sample.gif"
    assert data == b"GIF89a-test-bytes"


if __name__ == "__main__":
    main()
