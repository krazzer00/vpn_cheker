from PIL import Image, ImageDraw
from pathlib import Path

def create_icon():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Shield shape - VPN themed, purple/blue accent color #5b6af5
    shield = [
        (128, 18),
        (224, 58),
        (224, 148),
        (128, 238),
        (32, 148),
        (32, 58),
    ]
    draw.polygon(shield, fill=(91, 106, 245, 255))

    # Inner shield slightly lighter
    inner = [
        (128, 38),
        (204, 70),
        (204, 145),
        (128, 215),
        (52, 145),
        (52, 70),
    ]
    draw.polygon(inner, fill=(111, 126, 255, 255))

    # White checkmark
    pts = [(82, 128), (112, 162), (174, 96)]
    draw.line([pts[0], pts[1]], fill=(255, 255, 255, 255), width=16)
    draw.line([pts[1], pts[2]], fill=(255, 255, 255, 255), width=16)

    # Generate multiple sizes for ICO
    sizes = [256, 128, 64, 48, 32, 16]
    images = [img.resize((s, s), Image.LANCZOS) for s in sizes]
    images[0].save(
        "icon.ico",
        format="ICO",
        append_images=images[1:],
        sizes=[(s, s) for s in sizes],
    )
    print(f"icon.ico created ({Path('icon.ico').stat().st_size} bytes)")

create_icon()
