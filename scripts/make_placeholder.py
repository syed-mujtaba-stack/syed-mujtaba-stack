"""Synthetic head-and-shoulders placeholder photo.

Exercises the full banner pipeline (crop, dither, background segmentation) without
needing a real photograph. Swap in a real head-and-shoulders photo at
assets/photo/ and the pipeline is re-run unchanged.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def make_placeholder(size=(900, 1020), out="assets/photo/placeholder.jpg") -> None:
    W, H = size
    bg = (232, 233, 239)  # flat light wall
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img, "RGBA")

    cx, cy = W * 0.5, H * 0.40  # head centre

    # ---- shoulders / shirt (soft trapezoid) --------------------------------
    shirt = (158, 168, 186)
    d.polygon(
        [
            (0, H),
            (W, H),
            (W * 0.86, cy + 150),
            (W * 0.72, cy + 118),
            (W * 0.62, cy + 142),
            (W * 0.40, cy + 142),
            (W * 0.28, cy + 118),
            (W * 0.14, cy + 150),
        ],
        fill=shirt,
    )
    # shirt collar shading
    d.ellipse([cx - 110, cy + 92, cx + 110, cy + 210], fill=(146, 156, 174, 255))
    d.polygon([(cx - 95, cy + 108), (cx + 95, cy + 108), (cx, cy + 176)], fill=(92, 100, 118, 255))

    # ---- neck ---------------------------------------------------------------
    d.ellipse([cx - 46, cy + 116, cx + 46, cy + 196], fill=(196, 168, 140))
    d.ellipse([cx - 46, cy + 116, cx + 46, cy + 196], outline=(150, 122, 96), width=6)

    # ---- head ----------------------------------------------------------------
    head_box = (cx - 150, cy - 168, cx + 150, cy + 148)
    skin = (206, 178, 148)
    d.ellipse(head_box, fill=skin)
    # side shading so the face reads a directional light
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = ImageDraw.Draw(shade, "RGBA")
    sh.ellipse(head_box, fill=(60, 50, 40, 64))
    shade = shade.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img.convert("RGBA"), shade)

    # ---- hair -----------------------------------------------------------------
    d = ImageDraw.Draw(img, "RGBA")
    hair = (34, 34, 48)
    d.ellipse([cx - 158, cy - 180, cx + 158, cy + 30], fill=hair)
    d.ellipse([cx - 132, cy - 148, cx + 132, cy + 62], fill=skin)  # re-expose forehead
    # hair falls down both sides
    d.ellipse([cx - 172, cy - 120, cx - 118, cy + 110], fill=hair)
    d.ellipse([cx + 118, cy - 120, cx + 172, cy + 110], fill=hair)

    # ---- facial features --------------------------------------------------------
    ly = cy + 34  # eye line
    for ex in (cx - 52, cx + 52):
        d.ellipse([ex - 26, ly - 18, ex + 26, ly + 16], fill=(238, 210, 178))  # eye socket light
        d.ellipse([ex - 15, ly - 7, ex + 15, ly + 10], fill=(232, 204, 172))   # eyeball
        d.ellipse([ex - 6, ly - 4, ex + 6, ly + 6], fill=(58, 52, 58))         # iris
        d.ellipse([ex - 2, ly - 1, ex + 2, ly + 3], fill=(18, 16, 22))         # pupil
    # brows
    d.line([(cx - 74, ly - 34), (cx - 26, ly - 28)], fill=(52, 48, 56), width=9)
    d.line([(cx + 26, ly - 28), (cx + 74, ly - 34)], fill=(52, 48, 56), width=9)
    # nose
    d.line([(cx, ly + 12), (cx - 6, ly + 52)], fill=(178, 150, 122), width=7)
    d.ellipse([cx - 9, ly + 48, cx + 9, ly + 62], fill=(172, 144, 118))
    # mouth
    d.arc([cx - 38, ly + 70, cx + 38, ly + 104], start=10, end=170, fill=(176, 128, 110), width=8)
    d.arc([cx - 30, ly + 74, cx + 30, ly + 96], start=18, end=162, fill=(214, 180, 150), width=5)

    # ---- highlights (lit side) ---------------------------------------------------
    d.ellipse([cx + 70, cy - 120, cx + 120, cy - 40], fill=(255, 242, 220, 64))
    d.ellipse([cx + 44, cy - 56, cx + 78, cy - 6], fill=(255, 244, 224, 72))
    d.ellipse([cx - 108, cy - 40, cx - 60, cy + 8], fill=(255, 240, 214, 40))

    img = img.convert("RGB").filter(ImageFilter.GaussianBlur(0.6))
    img.save(out, "JPEG", quality=92)
    print("wrote", out, img.size)


if __name__ == "__main__":
    make_placeholder()