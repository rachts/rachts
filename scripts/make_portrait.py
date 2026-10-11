#!/usr/bin/env python3
"""Convert a local photograph into a transparent purple circle-grid SVG."""
import argparse
from pathlib import Path
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("assets/photo.jpg"))
    parser.add_argument("--output", type=Path, default=Path("assets/portrait.svg"))
    parser.add_argument("--size", type=int, default=480, help="square output width/height, 64–2048")
    parser.add_argument("--grid", type=int, default=64, help="circles per axis, 8–128")
    args = parser.parse_args(argv)
    if not 64 <= args.size <= 2048 or not 8 <= args.grid <= 128:
        parser.error("size must be 64–2048 and grid must be 8–128")
    if not args.input.is_file():
        print("portrait: photo not found; add assets/photo.jpg or pass --input PATH", file=sys.stderr)
        return 1
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("portrait: install optional dependency with python3 -m pip install -r scripts/requirements.txt", file=sys.stderr)
        return 1
    try:
        with Image.open(args.input) as image:
            rgba = ImageOps.fit(ImageOps.exif_transpose(image).convert("RGBA"), (args.grid, args.grid), method=Image.Resampling.LANCZOS)
        luminance = rgba.convert("L")
        step = args.size / args.grid
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{args.size}" height="{args.size}" viewBox="0 0 {args.size} {args.size}" role="img" aria-labelledby="title desc"><title id="title">Purple circle-grid portrait</title><desc id="desc">Local photograph rendered as purple halftone circles on a transparent canvas.</desc><g fill="#8A2BE2">']
        for y in range(args.grid):
            for x in range(args.grid):
                alpha = rgba.getpixel((x, y))[3] / 255
                radius = step * 0.47 * (1 - luminance.getpixel((x, y)) / 255) ** 0.5
                if radius >= 0.1 and alpha > 0:
                    parts.append(f'<circle cx="{(x + .5) * step:.2f}" cy="{(y + .5) * step:.2f}" r="{radius:.2f}" fill-opacity="{alpha:.3f}"/>')
        parts.append('</g></svg>\n')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("".join(parts), encoding="utf-8")
    except (OSError, ValueError, Image.DecompressionBombError):
        print("portrait: could not decode photo safely or write output", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
