"""Animation model: timeline, intro groups, drift bands, traveller morphs.

All animation timing lives here so the SVG build is purely mechanical.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

TOTAL = 19.5  # loop duration (s)
LOOP_BEGIN = 3.4  # loop layer starts after the one-time intro entrance

# 6 phases: portrait then 5 logos, 1.3s morphs between holds
PORTRAIT_END = 3.0
LOGO_HOLD_STARTS = [4.3, 7.6, 10.9, 14.2, 17.5]
LOGO_HOLD_ENDS = [6.3, 9.6, 12.9, 16.2, 19.5]
# morph windows between consecutive shapes
MORPHS = [(3.0, 4.3), (6.3, 7.6), (9.6, 10.9), (12.9, 14.2), (16.2, 17.5)]


def fracs(secs):
    return [round(s / TOTAL, 4) for s in secs]


# ------------------------------------------------------------------ portrait

def portrait_keyframes():
    """(keyTimes, opacity values, translate values) for the drift-band layer."""
    kt = fracs([0.0, PORTRAIT_END, LOGO_HOLD_STARTS[0], LOGO_HOLD_STARTS[-1], TOTAL])
    op = [1, 1, 0, 0, 1]
    return kt, op


def logo1_centroid(grid_w=300, grid_h=340):
    return np.array([grid_w / 2.0, grid_h / 2.0], dtype=float)


def assign_drift_bands(dot_xy: np.ndarray, n_bands: int = 94, noise_sigma: float = 4.0,
                       rng=None) -> np.ndarray:
    """Assign each portrait dot to a drift band.

    Drift is linear in position, so raw quantisation rebuilds a square grid;
    per-dot gaussian noise (sigma in grid units) scrambles the boundaries.
    Equal-count bands keep every band's transform budget similar.
    """
    rng = rng or np.random.default_rng(0)
    c1 = logo1_centroid()
    disp = 0.42 * (c1 - dot_xy)            # per-dot drift vector (grid units)
    mag = np.linalg.norm(disp, axis=1)
    key = mag + rng.normal(0, noise_sigma, size=len(mag))
    order = np.argsort(key)
    n = len(order)
    band = np.empty(n, dtype=int)
    per = int(np.ceil(n / n_bands))
    for b in range(n_bands):
        band[order[b * per:(b + 1) * per]] = b
    band[order[per * n_bands:]] = n_bands - 1
    return band, disp


def band_drifts(dot_xy, band, disp, grid_scale, rng=None):
    """Per-band mean drift vector in banner pixels, with per-band jitter."""
    rng = rng or np.random.default_rng(1)
    n_bands = band.max() + 1
    vecs = np.zeros((n_bands, 2))
    for b in range(n_bands):
        sel = band == b
        if sel.any():
            vecs[b] = disp[sel].mean(axis=0) * grid_scale
    jitter = rng.normal(0, 2.5, size=(n_bands, 2))
    return vecs + jitter


def intro_groups(n_groups: int = 60, rng=None) -> list:
    """Return list of int arrays: dot indices per intro group (interleaved)."""
    rng = rng or np.random.default_rng(3)
    return None  # filled by caller once dot count is known


def build_intro_groups(n_dots: int, n_groups: int = 60, rng=None):
    rng = rng or np.random.default_rng(3)
    perm = rng.permutation(n_dots)
    splits = np.array_split(perm, n_groups)
    return [np.sort(s) for s in splits]


# ------------------------------------------------------------------ travellers

def match_logo_clouds(clouds: list) -> list:
    """Return, for each of 900 travellers, the sequence of logo positions.

    Greedy smallest-distance bijection between consecutive logos -> short paths.
    clouds: list of (900, 2) arrays in a common coordinate space.
    """
    n = len(clouds[0])
    paths = [np.zeros((n, 2)) for _ in range(len(clouds))]
    for k, c in enumerate(clouds):
        paths[k][:, :] = c
    return paths


def greedy_bijection(src, dst):
    """One-to-one pairing between two (n,2) point sets by shortest total path."""
    n = len(src)
    d = ((src[:, None, :] - dst[None, :, :]) ** 2).sum(axis=2)  # n x n
    flat = np.argsort(d, axis=None)
    used_s = np.zeros(n, dtype=bool)
    used_d = np.zeros(n, dtype=bool)
    pair = np.full(n, -1, dtype=int)
    assigned = 0
    for idx in flat:
        if assigned >= n:
            break
        i, j = divmod(int(idx), n)
        if used_s[i] or used_d[j]:
            continue
        used_s[i] = True
        used_d[j] = True
        pair[i] = j
        assigned += 1
    return pair


def reorder_clouds(clouds: list):
    """Reorder every cloud so traveller t occupies the same index across logos."""
    base = clouds[0]
    seq = [base.copy()]
    for nxt in clouds[1:]:
        pair = greedy_bijection(seq[-1], nxt)
        seq.append(nxt[pair].copy())
    return seq


def traveller_keyframes():
    # position only matters while visible (opacity 0 outside); 10 keyframes.
    kt = fracs([0.0, 6.3, 7.6, 9.6, 10.9, 12.9, 14.2, 16.2, 17.5, TOTAL])
    return kt


def traveller_opacity():
    kt = fracs([0.0, PORTRAIT_END, LOGO_HOLD_STARTS[0], LOGO_HOLD_STARTS[-1], TOTAL])
    return kt, [0, 0, 1, 1, 0]