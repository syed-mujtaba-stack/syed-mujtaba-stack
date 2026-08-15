"""Trace logo SVGs into point clouds (the source of truth is the .npy data).

Parses SVG path data (M/L/H/V/C/S/Q/T/A/Z, absolute + relative), flattens curves,
rasterizes with a nonzero-winding scanline fill, and samples a fixed number of points
from the filled mask. Run as a module to regenerate assets/logos/*.npy.
"""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET

import numpy as np

# ---------------------------------------------------------------- path parser

_NUM = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
_NUM_RE = re.compile(_NUM)


_CMD_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")


def _tokenize(d: str) -> list:
    combined = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|" + _NUM)
    return combined.findall(d)


def _arc_points(x1, y1, x2, y2, rx, ry, phi, large, sweep, steps=48):
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return [(x1, y1), (x2, y2)]
    if x1 == x2 and y1 == y2:
        return [(x1, y1)]
    ph = math.radians(phi)
    cosp, sinp = math.cos(ph), math.sin(ph)
    dx = (x1 - x2) / 2.0
    dy = (y1 - y2) / 2.0
    x1p = cosp * dx + sinp * dy
    y1p = -sinp * dx + cosp * dy
    lam = (x1p ** 2) / (rx ** 2) + (y1p ** 2) / (ry ** 2)
    if lam > 1:
        s = math.sqrt(lam)
        rx *= s
        ry *= s
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    if den == 0:
        return [(x1, y1), (x2, y2)]
    coef = math.sqrt(max(num, 0.0) / den)
    if large == sweep:
        coef = -coef
    cxp = coef * (rx * y1p / ry)
    cyp = coef * (-ry * x1p / rx)
    cx = cosp * cxp - sinp * cyp + (x1 + x2) / 2.0
    cy = sinp * cxp + cosp * cyp + (y1 + y2) / 2.0
    ux = (x1p - cxp) / rx
    uy = (y1p - cyp) / ry
    vx = (-x1p - cxp) / rx
    vy = (-y1p - cyp) / ry
    theta1 = math.atan2(uy, ux)
    dtheta = math.atan2(vy, vx) - theta1
    if sweep == 0 and dtheta > 0:
        dtheta -= 2 * math.pi
    if sweep == 1 and dtheta < 0:
        dtheta += 2 * math.pi
    pts = []
    for i in range(steps + 1):
        t = theta1 + dtheta * i / steps
        pts.append((cx + rx * math.cos(t) * cosp - ry * math.sin(t) * sinp,
                    cy + rx * math.cos(t) * sinp + ry * math.sin(t) * cosp))
    return pts


def _flatten(d: str) -> list:
    """Return list of subpaths; each subpath is a list of (x, y)."""
    toks = _tokenize(d)
    subpaths = []
    cur = None
    x = y = 0.0
    sx = sy = 0.0
    last_c = None
    last_q = None
    i = 0
    cmd = None

    def num(idx):
        return float(toks[idx])

    def start_sub():
        nonlocal cur
        if cur is not None and len(cur) > 1:
            subpaths.append(cur)
        cur = []

    def line_to(nx, ny):
        nonlocal x, y
        x, y = nx, ny
        cur.append((x, y))

    while i < len(toks):
        t = toks[i]
        if t in "Mm":
            cmd = t
            i += 1
        elif t in "LlHhVvCcSsQqTtAa":
            cmd = t
            i += 1
        elif t in "Zz":
            cur.append((sx, sy))
            x, y = sx, sy
            i += 1
            if len(cur) > 1:
                subpaths.append(cur)
            cur = None
            last_c = last_q = None
            continue
        else:
            if cmd is None:
                raise ValueError("path does not start with a command: %r" % d[:40])
        # command dispatch
        c = cmd
        if c in "Mm":
            nx, ny = num(i), num(i + 1)
            i += 2
            if c == "m":
                nx, ny = x + nx, y + ny
            if cur is None:
                cur = []
                sx, sy = nx, ny
                cur.append((nx, ny))
                x, y = nx, ny
            else:
                line_to(nx, ny)
            cmd = "l" if c == "M" else "L"
        elif c in "Ll":
            nx, ny = num(i), num(i + 1)
            i += 2
            if c == "l":
                nx, ny = x + nx, y + ny
            line_to(nx, ny)
        elif c in "Hh":
            nx = num(i)
            i += 1
            if c == "h":
                nx = x + nx
            line_to(nx, y)
        elif c in "Vv":
            ny = num(i)
            i += 1
            if c == "v":
                ny = y + ny
            line_to(x, ny)
        elif c in "Cc":
            x1, y1, x2, y2, x3, y3 = num(i), num(i + 1), num(i + 2), num(i + 3), num(i + 4), num(i + 5)
            i += 6
            if c == "c":
                x1, y1 = x + x1, y + y1
                x2, y2 = x + x2, y + y2
                x3, y3 = x + x3, y + y3
            for k in range(1, 17):
                t = k / 16.0
                bx = (1 - t) ** 3 * x + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3 * x3
                by = (1 - t) ** 3 * y + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3 * y3
                cur.append((bx, by))
            last_c = (x2, y2)
            x, y = x3, y3
        elif c in "Ss":
            x2, y2, x3, y3 = num(i), num(i + 1), num(i + 2), num(i + 3)
            i += 4
            if c == "s":
                x2, y2 = x + x2, y + y2
                x3, y3 = x + x3, y + y3
            if last_c is not None:
                x1, y1 = 2 * x - last_c[0], 2 * y - last_c[1]
            else:
                x1, y1 = x, y
            for k in range(1, 17):
                t = k / 16.0
                bx = (1 - t) ** 3 * x + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3 * x3
                by = (1 - t) ** 3 * y + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3 * y3
                cur.append((bx, by))
            last_c = (x2, y2)
            x, y = x3, y3
        elif c in "Qq":
            x1, y1, x2, y2 = num(i), num(i + 1), num(i + 2), num(i + 3)
            i += 4
            if c == "q":
                x1, y1 = x + x1, y + y1
                x2, y2 = x + x2, y + y2
            for k in range(1, 17):
                t = k / 16.0
                bx = (1 - t) ** 2 * x + 2 * (1 - t) * t * x1 + t ** 2 * x2
                by = (1 - t) ** 2 * y + 2 * (1 - t) * t * y1 + t ** 2 * y2
                cur.append((bx, by))
            last_q = (x1, y1)
            x, y = x2, y2
        elif c in "Tt":
            x2, y2 = num(i), num(i + 1)
            i += 2
            if c == "t":
                x2, y2 = x + x2, y + y2
            if last_q is not None:
                x1, y1 = 2 * x - last_q[0], 2 * y - last_q[1]
            else:
                x1, y1 = x, y
            for k in range(1, 17):
                t = k / 16.0
                bx = (1 - t) ** 2 * x + 2 * (1 - t) * t * x1 + t ** 2 * x2
                by = (1 - t) ** 2 * y + 2 * (1 - t) * t * y1 + t ** 2 * y2
                cur.append((bx, by))
            last_q = (x1, y1)
            x, y = x2, y2
        elif c in "Aa":
            rx, ry = num(i), num(i + 1)
            phi, large, sweep = num(i + 2), int(num(i + 3)), int(num(i + 4))
            nx, ny = num(i + 5), num(i + 6)
            i += 7
            if c == "a":
                nx, ny = x + nx, y + ny
            for px, py in _arc_points(x, y, nx, ny, rx, ry, phi, large, sweep)[1:]:
                cur.append((px, py))
            x, y = nx, ny
            last_c = last_q = None
    if cur is not None and len(cur) > 1:
        subpaths.append(cur)
    return subpaths


# ------------------------------------------------------------ rasterize (fill)

def _edge_crossing(x1, y1, x2, y2, y):
    """Return (x at line y, +1/-1 winding direction) or None."""
    if y1 == y2:
        return None
    if y < min(y1, y2) or y > max(y1, y2):
        return None
    t = (y - y1) / (y2 - y1)
    x = x1 + t * (x2 - x1)
    return (x, 1 if y2 > y1 else -1)


def fill_mask(subpaths, W, H, bounds, pad=0.0):
    """Nonzero-winding scanline fill of closed subpaths into an (H, W) bool mask.

    bounds = (x0, y0, x1, y1) of the subpaths in original coords.
    """
    x0, y0, x1, y1 = bounds
    x0 -= pad
    y0 -= pad
    sx = W / (x1 - x0)
    sy = H / (y1 - y0)
    mask = np.zeros((H, W), dtype=bool)
    polys = []
    for sub in subpaths:
        pts = [((px - x0) * sx, (py - y0) * sy) for px, py in sub]
        polys.append(pts)
    for row in range(H):
        y = row + 0.5
        crossings = []
        for pts in polys:
            n = len(pts)
            for k in range(n):
                p1 = pts[k]
                p2 = pts[(k + 1) % n]
                c = _edge_crossing(p1[0], p1[1], p2[0], p2[1], y)
                if c is not None:
                    crossings.append(c)
        crossings.sort(key=lambda c: c[0])
        winding = 0
        xpix = 0.0
        inside = False
        for x, d in crossings:
            if inside and x > xpix:
                c0 = max(int(math.floor(xpix)), 0)
                c1 = min(int(math.ceil(x)), W)
                if c1 > c0:
                    mask[row, c0:c1] = True
            winding += d
            inside = winding != 0
            xpix = x
        if inside and xpix < W:
            mask[row, int(math.floor(xpix)):W] = True
    return mask


# ------------------------------------------------------------ point sampling

def sample_points(mask, n, jitter=0.35, rng=None):
    """Sample n points from a filled mask, roughly evenly spread."""
    rng = rng or np.random.default_rng(42)
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError("empty mask")
    if len(xs) <= n:
        idx = np.arange(len(xs))
        if n > len(xs):
            reps = int(np.ceil(n / len(xs)))
            idx = np.tile(idx, reps)
        idx = idx[:n]
    else:
        idx = np.linspace(0, len(xs) - 1, n).astype(int)
    pts = np.stack([xs[idx].astype(float), ys[idx].astype(float)], axis=1)
    if jitter > 0:
        pts = pts + rng.uniform(-jitter, jitter, size=pts.shape)
    return pts


def _poly_subpaths(polys):
    return [[(px, py) for px, py in poly] for poly in polys]


def rasterize_paths(subpaths, res=512, pad=0.05):
    """Rasterize flattened subpaths -> mask + bounds (in original coords)."""
    allp = np.array([p for sub in subpaths for p in sub])
    x0, y0 = allp.min(axis=0)
    x1, y1 = allp.max(axis=0)
    bounds = (float(x0), float(y0), float(x1), float(y1))
    mask = fill_mask(subpaths, res, res, bounds, pad=pad)
    return mask, bounds


def load_svg_path(path: str) -> list:
    tree = ET.parse(path)
    root = tree.getroot()
    for node in root.iter():
        if node.tag.endswith("path"):
            d = node.get("d")
            if d:
                return _flatten(d)
    raise ValueError("no <path> with d found in %s" % path)


def trace_logo(path: str, n: int = 900, res: int = 512, rng_seed: int = 7) -> np.ndarray:
    subpaths = load_svg_path(path)
    mask, bounds = rasterize_paths(subpaths, res=res)
    return sample_points(mask, n, rng=np.random.default_rng(rng_seed))


# ---------------------------------------------------------------- </> glyph

def glyph_mask_angle_brackets(res=512):
    """Custom </> glyph: two angle brackets + slash, drawn as strokes."""
    from PIL import Image, ImageDraw

    img = Image.new("L", (res, res), 0)
    dr = ImageDraw.Draw(img)
    w = int(res * 0.075)
    m = int(res * 0.14)
    # '<' left bracket
    dr.line([(m, res * 0.24), (res * 0.34, res * 0.5)], fill=255, width=w, joint="curve")
    dr.line([(m, res * 0.76), (res * 0.34, res * 0.5)], fill=255, width=w, joint="curve")
    # '/' slash
    dr.line([(res * 0.40, res * 0.72), (res * 0.60, res * 0.28)], fill=255, width=w)
    # '>' right bracket
    dr.line([(res * 0.66, res * 0.24), (res * 0.98, res * 0.5)], fill=255, width=w, joint="curve")
    dr.line([(res * 0.66, res * 0.76), (res * 0.98, res * 0.5)], fill=255, width=w, joint="curve")
    return np.asarray(img, dtype=bool)


def trace_glyph(n: int = 900, res: int = 512, rng_seed: int = 11) -> np.ndarray:
    mask = glyph_mask_angle_brackets(res)
    return sample_points(mask, n, rng=np.random.default_rng(rng_seed))


# -------------------------------------------------------------------- CLI

def main() -> None:
    import os

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logos")
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in [
        ("flutter", lambda: trace_logo(os.path.join(out_dir, "flutter.svg"), rng_seed=1)),
        ("react", lambda: trace_logo(os.path.join(out_dir, "react.svg"), rng_seed=2)),
        ("vercel", lambda: trace_logo(os.path.join(out_dir, "vercel.svg"), rng_seed=3)),
        ("python", lambda: trace_logo(os.path.join(out_dir, "python.svg"), rng_seed=4)),
        ("angle", lambda: trace_glyph(rng_seed=5)),
    ]:
        pts = fn()
        np.save(os.path.join(out_dir, name + ".npy"), pts)
        print(f"{name}: {pts.shape[0]} pts, bbox "
              f"x[{pts[:,0].min():.0f},{pts[:,0].max():.0f}] y[{pts[:,1].min():.0f},{pts[:,1].max():.0f}]")


if __name__ == "__main__":
    main()