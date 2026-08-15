"""Quantitative verification of generated banners.

Measures, rather than eyeballs:
  - portrait ink coverage vs the source dither stats
  - intro-group evenness  (~0.05 good, ~0.7 patchy)
  - drift-band straight-boundary metric (~0.01 organic, ~0.17 grid)
  - per-band dot distribution
  - text fit (rows inside the info panel)
  - SMIL validity (monotonic keyTimes, values/keyTimes counts)
  - logo clouds inside the portrait frame
"""
from __future__ import annotations

import os
import re
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("banner", 1)[0])
from banner import anim, build, portrait  # noqa: E402


def parse_runs(d: str, ox, oy, scale):
    """Parse 'M x y h len ...' path data into numpy run arrays (banner px)."""
    xs, ys, ls = [], [], []
    for m in re.finditer(r"M([-\d.]+) ([-\d.]+)h([-\d.]+)", d):
        xs.append(float(m.group(1)))
        ys.append(float(m.group(2)))
        ls.append(float(m.group(3)))
    return np.array(xs), np.array(ys), np.array(ls)


def smil_ok(svg: str) -> list[str]:
    errors = []
    for m in re.finditer(r'keyTimes="([^"]*)"[^>]*values="([^"]*)"', svg):
        kt, vals = m.group(1).split(";"), m.group(2).split(";")
        kt = [float(x) for x in kt]
        if len(kt) != len(vals):
            errors.append(f"keyTimes/values mismatch: {len(kt)} vs {len(vals)}")
        if abs(kt[0]) > 1e-9 or abs(kt[-1] - 1.0) > 1e-9:
            errors.append(f"keyTimes bounds: {kt[0]}..{kt[-1]}")
        if any(b <= a for a, b in zip(kt, kt[1:])):
            errors.append("keyTimes not strictly increasing")
    return errors


def main(photo="assets/photo/placeholder.jpg"):
    root = os.path.join(os.path.dirname(__file__), "..", "..") + os.sep
    for mode in ("dark", "light"):
        svg = open(f"{root}{mode}.svg", encoding="utf-8").read()
        pal = build.PALETTE[mode]
        runs, st = portrait.build_dots(photo, mode)
        print(f"--- {mode}.svg ---")
        print(f"  size {len(svg)/1024:.0f} KB | dots {st['dots']} | runs {len(runs)}")

        # ---- ink coverage in portrait frame ---------------------------
        all_x, all_y, all_l = [], [], []
        for d in re.findall(r'<path d="([^"]*)"', svg):
            xs, ys, ls = parse_runs(d, build.PXO, build.PYO, build.S)
            all_x.append(xs)
            all_y.append(ys)
            all_l.append(ls)
        all_x, all_y, all_l = (np.concatenate(a) for a in (all_x, all_y, all_l))
        # count painted cells in the portrait box
        x0, x1 = build.PXO, build.PXO + build.GRID_W * build.S
        y0, y1 = build.PYO, build.PYO + build.GRID_H * build.S
        ink_cells = 0
        for xx, yy, ll in zip(all_x, all_y, all_l):
            if x0 <= xx < x1 and y0 <= yy < y1:
                ink_cells += ll
        expected = st["dots"] * build.S  # ~2 layers paint the same cells
        print(f"  portrait ink: {ink_cells:.0f} painted px vs expected ~{expected:.0f} "
              f"({ink_cells/max(expected,1):.2f}x)")

        # ---- band distribution ---------------------------------------
        run_xy = np.array([[x, y] for x, y, _ in runs], dtype=float)
        band, disp = anim.assign_drift_bands(run_xy, build.N_BANDS, rng=np.random.default_rng(0))
        counts = np.bincount(band, minlength=build.N_BANDS)
        print(f"  bands: {build.N_BANDS}, count min={counts.min()} max={counts.max()} "
              f"cv={counts.std()/counts.mean():.3f}")

        # ---- straight-boundary metric ---------------------------------
        # build band index grid from per-dot cells (expand runs)
        grid = np.full((build.GRID_H, build.GRID_W), -1, dtype=int)
        gi = 0
        for x, y, ln in runs:
            for k in range(ln):
                if 0 <= x + k < build.GRID_W and 0 <= y < build.GRID_H:
                    grid[y, x + k] = band[gi]
            gi += 1
        h, w = grid.shape
        bdry = np.zeros_like(grid, dtype=bool)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nbr = np.full_like(grid, -1)
            yy, xx = np.mgrid[0:h, 0:w]
            ny, nx = np.clip(yy + dr, 0, h - 1), np.clip(xx + dc, 0, w - 1)
            nbr = grid[ny, nx]
            bdry |= (grid != -1) & (nbr != -1) & (grid != nbr)
        # straight if both perpendicular neighbours are boundary with same bands
        straight = 0
        total = int(bdry.sum())
        ys, xs = np.nonzero(bdry)
        for y, x in zip(ys, xs):
            band_here = grid[y, x]
            for ddx in (-1, 1):
                if x + ddx < 0 or x + ddx >= w:
                    continue
                for ddy in (-1, 1):
                    if y + ddy < 0 or y + ddy >= h:
                        continue
            # horizontal straightness
            h_ok = (x - 1 >= 0 and x + 1 < w and
                    grid[y, x - 1] != band_here and grid[y, x + 1] != band_here and
                    grid[y, x - 1] == grid[y, x + 1] and bdry[y, x - 1] and bdry[y, x + 1])
            v_ok = (y - 1 >= 0 and y + 1 < h and
                    grid[y - 1, x] != band_here and grid[y + 1, x] != band_here and
                    grid[y - 1, x] == grid[y + 1, x] and bdry[y - 1, x] and bdry[y + 1, x])
            if h_ok or v_ok:
                straight += 1
        print(f"  straight-boundary metric: {straight/max(total,1):.3f} "
              f"(grid~0.17, organic~0.01) | boundary cells {total}")

        # ---- intro evenness ------------------------------------------
        groups = anim.build_intro_groups(len(runs), build.N_INTRO, rng=np.random.default_rng(3))
        gpts = []
        for idx in groups:
            gpts.append(np.array([run_xy[i] for i in idx]))
        devs = []
        for pts in groups and gpts:
            c = pts.mean(axis=0)
            q = ((pts[:, 0] < c[0]) & (pts[:, 1] < c[1])).sum()
            q2 = ((pts[:, 0] >= c[0]) & (pts[:, 1] < c[1])).sum()
            q3 = ((pts[:, 0] < c[0]) & (pts[:, 1] >= c[1])).sum()
            q4 = len(pts) - q - q2 - q3
            fracs = np.array([q, q2, q3, q4]) / len(pts)
            devs.append(fracs.max() - 0.25)
        print(f"  intro evenness: {np.mean(devs):.3f} (~0.05 good, ~0.7 patchy)")

        # ---- text fit -------------------------------------------------
        xmax = build.INFO_X + build.INFO_W
        for label, value in build.INFO_ROWS:
            used = (len(label) + len(value)) * build.CHAR_W
            if used > build.INFO_W - 20:
                print(f"  OVERFLOW row {label!r}: {used:.0f}px > {build.INFO_W-20}px")

        # ---- travellers inside frame -----------------------------------
        clouds = build.logo_clouds_grid()
        frame = (build.PXO + 6, build.PYO + 6, build.PXO + build.GRID_W * build.S - 6,
                 build.PYO + build.GRID_H * build.S - 6)
        for k, c in enumerate(clouds):
            p = c * build.S + np.array([build.PXO, build.PYO])
            inside = ((p[:, 0] >= frame[0]) & (p[:, 0] <= frame[2]) &
                      (p[:, 1] >= frame[1]) & (p[:, 1] <= frame[3]))
            print(f"  logo{k}: {inside.mean():.2f} of points inside frame")

        # ---- SMIL validity --------------------------------------------
        errs = smil_ok(svg)
        print(f"  SMIL checks: {'OK' if not errs else errs}")


if __name__ == "__main__":
    photo = sys.argv[1] if len(sys.argv) > 1 else "assets/photo/placeholder.jpg"
    main(photo)