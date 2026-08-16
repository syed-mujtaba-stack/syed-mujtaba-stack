"""Assemble dark.svg / light.svg for the animated banner."""
from __future__ import annotations

import html
import os

import numpy as np

from . import anim, portrait, premium

W, H = 1180, 610
TITLE_H = 44

GRID_W, GRID_H = 300, 340
S = (424 - 2 * 16) / GRID_W          # grid -> banner px scale (~1.31)
PXO, PYO = 32, 94                    # portrait dot origin
CROP = (0.28, 0.13, 0.62, 0.46)      # photo region (fractions): tight head-and-shoulders so the face reads

# panels
PORT_X, PORT_W = 24, 424
INFO_X, INFO_W = 470, 690

# type
ROW_FS = 14
HEAD_FS = 13
LIVE_FS = 12
CHAR_W = ROW_FS * 0.6                # monospace advance at 14px
ROW_GAP = 23
TEXT_X_END = INFO_X + INFO_W - 8

LOGO_BOX = 258                       # logo cloud fits in this square (grid units)
N_TRAVEL = 900
N_BANDS = 94
N_INTRO = 60

PALETTE = {
    "dark": {
        "bg": "#0A101F", "panel": "#0F1830", "frame": "#22304F",
        "portrait": "#A78BFA", "chrome": "#22D3EE", "accent": "#10B981",
        "text": "#E6E9F5", "dim": "#7986A8", "live": "#EF4444",
        "traffic": ["#FF5F57", "#FEBC2E", "#28C840"], "pilltext": "#05281F",
        "outline": "#1B2745",
        "star": "#8B9BB8", "glow_op": 0.16, "scan": "#FFFFFF", "scan_op": 0.05,
    },
    "light": {
        "bg": "#F4F6FB", "panel": "#FFFFFF", "frame": "#D6DDF0",
        "portrait": "#7C3AED", "chrome": "#0891B2", "accent": "#059669",
        "text": "#101B33", "dim": "#5B6B8C", "live": "#DC2626",
        "traffic": ["#FF5F57", "#FEBC2E", "#28C840"], "pilltext": "#05281F",
        "outline": "#C7D0E8",
        "star": "#5B6B8C", "glow_op": 0.10, "scan": "#0F1830", "scan_op": 0.05,
    },
}

INFO_ROWS = [
    ("Subject", "Syed Mujtaba Abbas"),
    ("Role", "Full-Stack / Agentic AI / DevOps"),
    ("Origin", "Karachi, Pakistan"),
    ("Education", "BSc Computer Science & Software Eng"),
    ("Status", "Building + Learning + Shipping"),
    ("ToolChain", "VS Code · Git · Android Studio · Figma · Vercel · Netlify"),
    ("Core.Lang", "Python · JS/TS · Dart · Go · Java · PHP · Swift"),
    ("Core.Frontend", "React · Next.js · Flutter · Vue · Tailwind"),
    ("Core.Backend", "FastAPI · Node.js · Django · Laravel · Strapi"),
    ("Core.Database", "PostgreSQL · MySQL · MongoDB · Redis · Firebase"),
    ("Core.Infra", "Docker · AWS · Vercel · Linux · GH Actions"),
    ("Grid.Mail", "abbasmujtaba125@gmail.com"),
    ("Grid.Portfolio", "mujtaba-abbas.web.app"),
    ("Grid.LinkedIn", "creative-mujtaba"),
    ("Grid.GitHub", "syed-mujtaba-stack"),
    ("Grid.Facebook", "m.j_syed"),
]


# ------------------------------------------------------------------ helpers

def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def path_for_runs(runs, scale=S, ox=PXO, oy=PYO):
    """Encode runs as compact 'M x y h len' path data."""
    parts = []
    for x, y, ln in runs:
        parts.append(f"M{x * scale + ox:.1f} {y * scale + oy:.1f}h{ln * scale:.1f}")
    return " ".join(parts)


def expand_runs(runs):
    """runs -> per-cell (x, y) array (grid coords)."""
    out = []
    for x, y, ln in runs:
        for i in range(ln):
            out.append((x + i, y))
    return np.array(out, dtype=float)


# ------------------------------------------------------------ travellers

def logo_clouds_grid(logo_dir="assets/logos", n=N_TRAVEL):
    names = ["flutter", "angle", "vercel", "react", "python"]
    clouds = []
    for nm in names:
        pts = np.load(os.path.join(logo_dir, nm + ".npy")).astype(float)
        pts = pts[:n]
        # 512-space -> centered, fit into LOGO_BOX (grid units)
        c = pts.mean(axis=0)
        pts = pts - c
        span = max(pts[:, 0].max() - pts[:, 0].min(), pts[:, 1].max() - pts[:, 1].min())
        pts = pts / span * LOGO_BOX
        pts += np.array([GRID_W / 2.0, GRID_H / 2.0])
        clouds.append(pts)
    return anim.reorder_clouds(clouds)


def _kt_str(kt):
    return ";".join(f"{v:.3f}" for v in kt)


def traveller_element(pos, xy_vals, kt, op_kt, op_vals, color, r=1.5, begin=0.0):
    xy = ";".join(f"{v[0]:.1f} {v[1]:.1f}" for v in xy_vals)
    b = f' begin="{begin:g}s"' if begin else ""
    return (
        f'<circle r="{r}" fill="{color}" opacity="0">'
        f'<animateTransform attributeName="transform" type="translate" dur="{anim.TOTAL}s" '
        f'repeatCount="indefinite" keyTimes="{_kt_str(kt)}" values="{xy}"{b}/>'
        f'<animate attributeName="opacity" dur="{anim.TOTAL}s" repeatCount="indefinite" '
        f'keyTimes="{_kt_str(op_kt)}" values="{";".join(map(str, op_vals))}"{b}/>'
        f"</circle>"
    )


# ------------------------------------------------------------- text row

def info_row(label, value, x0, y, color, dim, cw=CHAR_W, fs=ROW_FS):
    label_w = len(label) * cw
    value_w = len(value) * cw
    value_x = TEXT_X_END - value_w
    leader_lo = x0 + label_w + 4
    leader_hi = value_x - 6
    dots = []
    dx = leader_lo
    while dx < leader_hi - cw:
        dots.append(f'<circle cx="{dx:.1f}" cy="{y - fs * 0.28:.1f}" r="1.3" fill="{dim}"/>')
        dx += cw
    leader = "".join(dots)
    return (
        f'{leader}'
        f'<text x="{x0}" y="{y}" font-size="{fs}" fill="{color}" textLength="{label_w:.1f}" '
        f'lengthAdjust="spacingAndGlyphs">{esc(label)}</text>'
        f'<text x="{value_x:.1f}" y="{y}" font-size="{fs}" fill="{color}" textLength="{value_w:.1f}" '
        f'lengthAdjust="spacingAndGlyphs">{esc(value)}</text>'
    )


# ---------------------------------------------------------------- build

def build_banner(photo_path, mode, out_path, logo_dir="assets/logos"):
    pal = PALETTE[mode]
    font = "'Cascadia Code','JetBrains Mono','Fira Code',Consolas,ui-monospace,monospace"

    runs, st = portrait.build_dots(photo_path, mode, crop=CROP)
    run_xy = np.array([[x, y] for x, y, _ in runs], dtype=float)

    # ---- drift bands (loop layer) -----------------------------------
    band, disp = anim.assign_drift_bands(run_xy, N_BANDS, rng=np.random.default_rng(0))
    band_vecs = anim.band_drifts(run_xy, band, disp, S, rng=np.random.default_rng(1))
    kt, op = anim.portrait_keyframes()
    kt_str = _kt_str(kt)
    loop_groups = []
    for b in range(int(band.max()) + 1):
        sel = np.where(band == b)[0]
        sub = [runs[i] for i in sel]
        d = path_for_runs(sub)
        dx, dy = band_vecs[b]
        loop_groups.append(
            f'<g opacity="0"><path d="{d}" fill="{pal["portrait"]}" shape-rendering="crispEdges" stroke="{pal["portrait"]}" '
            f'stroke-width="{S * 1.02:.2f}"/>'
            f'<animateTransform attributeName="transform" type="translate" additive="sum" '
            f'begin="{anim.LOOP_BEGIN:g}s" '
            f'dur="{anim.TOTAL}s" repeatCount="indefinite" keyTimes="{kt_str}" '
            f'values="0 0;0 0;{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};0 0"/>'
            f'<animate attributeName="opacity" begin="{anim.LOOP_BEGIN:g}s" dur="{anim.TOTAL}s" repeatCount="indefinite" '
            f'keyTimes="{kt_str}" values="1;1;0;0;1"/>'
            f"</g>"
        )

    # ---- intro groups (one-time entrance) ---------------------------
    groups = anim.build_intro_groups(len(runs), N_INTRO, rng=np.random.default_rng(3))
    intro_groups = []
    for gi, idx in enumerate(groups):
        sub = [runs[i] for i in idx]
        d = path_for_runs(sub)
        begin_in = round(0.05 + gi * (1.9 / N_INTRO), 3)
        intro_groups.append(
            f'<g><path d="{d}" fill="{pal["portrait"]}" shape-rendering="crispEdges" stroke="{pal["portrait"]}" '
            f'stroke-width="{S * 1.02:.2f}"/>'
            f'<animate attributeName="opacity" begin="{begin_in:.2f}s" dur="0.16s" fill="freeze" from="0" to="1"/>'
            f'<animate attributeName="opacity" begin="2.9s" dur="0.5s" fill="freeze" from="1" to="0"/>'
            f"</g>"
        )

    # ---- travellers --------------------------------------------------
    clouds = logo_clouds_grid(logo_dir)
    # grid coords -> banner px
    trav_banner = [(c * S + np.array([PXO, PYO])) for c in clouds]
    tkt = anim.traveller_keyframes()
    op_kt, op_vals = anim.traveller_opacity()
    trav_els = []
    for i in range(N_TRAVEL):
        l = [trav_banner[k][i] for k in range(5)]
        xy = [l[0], l[0], l[1], l[1], l[2], l[2], l[3], l[3], l[4], l[4]]
        trav_els.append(traveller_element(i, xy, tkt, op_kt, op_vals, pal["portrait"],
                                          begin=anim.LOOP_BEGIN))

    # ---- chrome -------------------------------------------------------
    live_cx = INFO_X + INFO_W - 228
    live_dot = (
        f'{premium.live_ping(pal, live_cx, 90)}'
        f'<circle cx="{live_cx}" cy="90" r="4.5" fill="{pal["live"]}">'
        f'<animate attributeName="opacity" values="1;0.2;1" keyTimes="0;0.5;1" dur="1.6s" repeatCount="indefinite"/>'
        f"</circle>"
    )
    pill_w = len("syed-mujtaba-stack") * CHAR_W + 26
    pill_x = INFO_X + INFO_W - pill_w
    pill = (
        f'<rect x="{pill_x}" y="74" width="{pill_w:.0f}" height="28" rx="14" fill="{pal["accent"]}"/>'
        f'<text x="{pill_x + pill_w / 2:.0f}" y="94" font-size="14" fill="{pal["pilltext"]}" '
        f'text-anchor="middle">syed-mujtaba-stack</text>'
    )

    headers = (
        f'<text x="{PORT_X + 8}" y="66" font-size="{HEAD_FS}" fill="{pal["chrome"]}" '
        f'font-family="{font}">VISUAL.MAP</text>'
        f'<text x="{INFO_X}" y="66" font-size="{HEAD_FS}" fill="{pal["chrome"]}" '
        f'font-family="{font}">SYSTEM.INFO</text>'
        f'{live_dot}'
        f'<text x="{INFO_X + INFO_W - 216}" y="95" font-size="{LIVE_FS}" fill="{pal["live"]}" '
        f'font-family="{font}">LIVE</text>'
        f'{pill}'
    )

    # portrait frame (gradient stroke + soft glow behind)
    frame_x = PORT_X + 2
    frame_y = 80
    frame_w = GRID_W * S + 14
    frame_h = GRID_H * S + 14
    glow_el = premium.glow(pal, PXO + GRID_W * S / 2, PYO + GRID_H * S / 2,
                           GRID_W * S * 0.62, GRID_H * S * 0.56)
    frame = (
        f'<rect x="{frame_x}" y="{frame_y}" width="{frame_w:.0f}" height="{frame_h:.0f}" rx="10" '
        f'fill="{pal["panel"]}" fill-opacity="0.35" stroke="url(#gFrame)" stroke-width="1.5"/>'
    )

    rows_xml = []
    y = 132
    for label, value in INFO_ROWS:
        rows_xml.append(info_row(label, value, INFO_X, y, pal["text"], pal["dim"]))
        y += ROW_GAP

    # title bar
    title = (
        f'<rect x="6" y="6" width="{W - 12}" height="{TITLE_H}" rx="10" fill="{pal["panel"]}"/>'
        + "".join(
            f'<circle cx="{26 + i * 22}" cy="28" r="5.5" fill="{c}"/>'
            for i, c in enumerate(pal["traffic"])
        )
        + f'<text x="96" y="33" font-size="13" fill="{pal["dim"]}" font-family="{font}">profile.sh --live'
        f'<tspan fill="{pal["accent"]}"> ▍</tspan></text>'
    )

    body = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="610" viewBox="0 0 1180 610">
<defs><style>.t{{font-family:{font}}}</style>{premium.gradient_defs(pal)}</defs>
<rect width="1180" height="610" rx="16" fill="{pal["bg"]}"/>
{premium.starfield(pal)}
{glow_el}
{premium.scanline(pal)}
{title}
{headers}
{frame}
<g>{''.join(intro_groups)}</g>
<g>{''.join(loop_groups)}</g>
<g>{''.join(trav_els)}</g>
{premium.accent_sparkle(pal)}
{''.join(rows_xml)}
{premium.status_bar(pal, font)}
</svg>
"""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(body)
    return {"size": os.path.getsize(out_path), "stats": st, "runs": len(runs), "bands": N_BANDS}


def main(photo="assets/photo/placeholder.jpg"):
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    for mode in ("dark", "light"):
        out = os.path.join(root, f"{mode}.svg")
        res = build_banner(os.path.join(root, photo), mode, out,
                           logo_dir=os.path.join(root, "assets", "logos"))
        print(f"{mode}.svg: {res['size'] / 1024:.0f} KB, runs={res['runs']}, dots={res['stats']['dots']}")


if __name__ == "__main__":
    main()