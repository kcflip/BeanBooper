"""
add_outline.py — Add outlines to subjects in transparent PNGs

Usage:
    # Single file
    python add_outline.py input.png
    python add_outline.py input.png --color "#FF0000" --size 4 --trim

    # Whole directory — outputs to {dir}/{timestamp}-outline/
    python add_outline.py ./assets/
    python add_outline.py ./assets/ --color "#FFFFFF" --size 6 --trim

Options:
    --color          Outline color as hex (default: #000000 / black)
    --size           Outline thickness in display pixels (default: 3)
    --trim           Crop transparent padding before outlining
    --display-width  CSS display width in px used to scale --size to source
                     resolution (default: 600). Set to 0 to use raw pixels.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageFilter


def trim_alpha(img: Image.Image) -> Image.Image:
    bbox = img.split()[3].getbbox()
    return img.crop(bbox) if bbox else img


def add_outline(image_path: Path, output_path: Path, color: str = "#000000", size: int = 3, trim: bool = False, display_width: int = 600) -> None:
    img = Image.open(image_path).convert("RGBA")
    if trim:
        img = trim_alpha(img)

    # Scale outline thickness from display pixels to source pixels
    if display_width > 0:
        size = max(1, round(size * img.width / display_width))

    # Extract the alpha (transparency) channel
    alpha = img.split()[3]

    # Grow the alpha channel outward to create the outline shape
    outline_alpha = alpha
    for _ in range(size):
        outline_alpha = outline_alpha.filter(ImageFilter.MaxFilter(3))

    # Parse the hex color
    hex_color = color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # Create a solid-color image the same size, using the grown alpha as its mask
    outline_layer = Image.new("RGBA", img.size, (r, g, b, 255))
    outline_layer.putalpha(outline_alpha)

    # Paste the original image on top of the outline layer
    result = Image.alpha_composite(outline_layer, img)

    result.save(output_path, "PNG")
    print(f"  ✓ {output_path.name}")


def process_single(input_path: Path, color: str, size: int, trim: bool, display_width: int) -> None:
    output_path = input_path.parent / f"{input_path.stem}_outlined{input_path.suffix}"
    add_outline(input_path, output_path, color=color, size=size, trim=trim, display_width=display_width)


def process_directory(input_dir: Path, color: str, size: int, trim: bool, display_width: int) -> None:
    images = sorted(input_dir.glob("*.png"))
    if not images:
        print(f"No PNG files found in {input_dir}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = input_dir / f"{timestamp}-outline"
    output_dir.mkdir()
    print(f"Output folder: {output_dir}\n")

    for image_path in images:
        add_outline(image_path, output_dir / image_path.name, color=color, size=size, trim=trim, display_width=display_width)

    print(f"\nDone — {len(images)} image(s) processed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add an outline to transparent PNG(s)")
    parser.add_argument("input", help="Path to a PNG file or a directory of PNGs")
    parser.add_argument("--color", default="#000000", help='Outline color as hex, e.g. "#FF5733"')
    parser.add_argument("--size", type=int, default=3, help="Outline thickness in display pixels (scaled to source resolution)")
    parser.add_argument("--trim", action="store_true", help="Crop transparent padding before outlining")
    parser.add_argument("--display-width", type=int, default=600, dest="display_width",
                        help="CSS display width in px used to scale --size (default: 600). Use 0 for raw pixels.")

    args = parser.parse_args()
    target = Path(args.input)

    if target.is_dir():
        process_directory(target, color=args.color, size=args.size, trim=args.trim, display_width=args.display_width)
    elif target.is_file():
        process_single(target, color=args.color, size=args.size, trim=args.trim, display_width=args.display_width)
    else:
        print(f"Error: '{target}' is not a valid file or directory.")
        sys.exit(1)