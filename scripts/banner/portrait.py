"""Portrait pipeline: photo -> 1-bit dithered dot runs for the banner.

Crop -> grayscale -> autocontrast -> contrast -> unsharp -> Floyd-Steinberg
(serpentine) -> run-length encoding. Dark mode additionally segments the subject
out of the background so dots draw the lit subject only.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from scipy import ndimage


def crop_to_aspect(path: str, gw: int = 300, gh: int = 340, crop: tuple | None = None):
    """Open photo, crop to gw:gh aspect (default centre), return (rgb, gray) at (gw, gh)."""
    im = Image.open(path).convert("RGB")
    W, H = im.size
    target = gw / gh
    cur = W / H
    if crop is not None:
        x0, y0, x1, y1 = crop
        im = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        W, H = im.size
        cur = W / H
    if cur > target:  # too wide -> crop width
        nw = int(H * target)
        x0 = (W - nw) // 2
        im = im.crop((x0, 0, x0 + nw, H))
    else:  # too tall -> crop height
        nh = int(W / target)
        y0 = (H - nh) // 2
        im = im.crop((0, y0, W, y0 + nh))
    im = im.resize((gw, gh), Image.LANCZOS)
    gray = im.convert("L")
    return im, gray


def preprocess(gray: Image.Image) -> np.ndarray:
    g = ImageOps.autocontrast(gray, cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.3)
    g = g.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    return np.asarray(g, dtype=np.float64) / 255.0


def dither_serpentine(arr: np.ndarray) -> np.ndarray:
    """Floyd-Steinberg 1-bit dither in serpentine order. Returns ink=True where dark."""
    h, w = arr.shape
    a = arr.copy()
    ink = np.zeros((h, w), dtype=bool)
    for y in range(h):
        if y % 2 == 0:
            xs = range(w)
        else:
            xs = range(w - 1, -1, -1)
        for x in xs:
            old = a[y, x]
            new = 0.0 if old < 0.5 else 1.0
            ink[y, x] = new < 0.5
            err = old - new
            right = 1 if y % 2 == 0 else -1
            nb = [
                (x + right, y, 7 / 16),
                (x - right, y + 1, 3 / 16),
                (x, y + 1, 5 / 16),
                (x + right, y + 1, 1 / 16),
            ]
            for nx, ny, wgt in nb:
                if 0 <= nx < w and 0 <= ny < h:
                    a[ny, nx] += err * wgt
    return ink


def subject_mask(rgb: Image.Image, erode: int = 2, thr_scale: float = 0.6) -> np.ndarray:
    """Segment the lit subject from a flat background. Returns True on the subject.

    thr_scale relaxes the Otsu distance threshold (< 1 keeps dim subject parts like
    dark hair that sit close to a dark background).
    """
    a = np.asarray(rgb, dtype=np.float64)
    h, w = a.shape[:2]
    m = min(h, w)
    ring = 8
    border = np.concatenate([
        a[:ring].reshape(-1, 3),
        a[-ring:].reshape(-1, 3),
        a[:, :ring].reshape(-1, 3),
        a[:, -ring:].reshape(-1, 3),
    ])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((a - bg) ** 2).sum(axis=2))

    # Otsu threshold on distance
    hist, edges = np.histogram(dist, bins=256, range=(0, dist.max() + 1e-6))
    cdf = np.cumsum(hist)
    total = cdf[-1]
    mu = np.cumsum(hist * edges[:-1])
    muT = mu[-1]
    best_t, best_v = 0, -1
    for t in range(1, 255):
        w0 = cdf[t]
        if w0 == 0 or w0 == total:
            continue
        w1 = total - w0
        mu0 = mu[t] / w0
        mu1 = (muT - mu[t]) / w1
        v = w0 * w1 * (mu0 - mu1) ** 2
        if v > best_v:
            best_v, best_t = v, t
    thr = edges[best_t]

    subject = dist >= thr * thr_scale
    subject = ndimage.binary_closing(subject, structure=np.ones((5, 5)))
    subject = ndimage.binary_fill_holes(subject)
    lab, n = ndimage.label(subject)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        biggest = int(np.argmax(sizes)) + 1
        subject = lab == biggest
    if erode > 0:
        subject = ndimage.binary_erosion(subject, structure=np.ones((3, 3)), iterations=erode)
    return subject


def runs_from_ink(ink: np.ndarray) -> list:
    """Run-length encode ink rows -> [(x, y, length)] in grid coordinates."""
    runs = []
    h, w = ink.shape
    for y in range(h):
        x = 0
        row = ink[y]
        while x < w:
            if row[x]:
                x0 = x
                while x < w and row[x]:
                    x += 1
                runs.append((x0, y, x - x0))
            else:
                x += 1
    return runs


def build_dots(photo_path: str, mode: str, gw: int = 300, gh: int = 340, crop=None):
    """Return (runs, stats) where runs are the ink dots to draw.

    mode 'light': dots = dark parts of the whole photo.
    mode 'dark':  dots = lit parts of the subject (background removed).
    """
    rgb, gray = crop_to_aspect(photo_path, gw, gh, crop=crop)
    arr = preprocess(gray)
    ink = dither_serpentine(arr)
    if mode == "light":
        # paint dark parts on white unless the photo's background is dark
        # (then paint the lit subject instead, so a dark-bg headshot reads)
        mask = subject_mask(rgb)
        border_dark = float(np.asarray(gray).mean()) < 115
        dots = (~ink) & mask if border_dark else ink
    else:
        mask = subject_mask(rgb)
        dots = (~ink) & mask
    runs = runs_from_ink(dots)
    stats = {
        "grid": (gw, gh),
        "dots": int(dots.sum()),
        "runs": len(runs),
        "subject_frac": float(dots.sum() / (gw * gh)),
    }
    return runs, stats