from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def main() -> None:
    out = Path(__file__).with_name("sample_vfx.gif")
    frames = []
    for i in range(16):
        image = Image.new("RGBA", (160, 160), (0, 0, 0, 255))
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow)
        radius = 18 + i * 2
        cx = 80 + int((i - 8) * 1.5)
        cy = 82
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(80, 210, 255, 185))
        glow = glow.filter(ImageFilter.GaussianBlur(8))
        image.alpha_composite(glow)
        draw = ImageDraw.Draw(image)
        draw.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(235, 255, 255, 255))
        frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE))

    frames[0].save(out, save_all=True, append_images=frames[1:], duration=70, loop=0, disposal=2)
    print(out)


if __name__ == "__main__":
    main()
