"""Premium chrome for the banner: glow, starfield, scanline sweep,
gradient frame, live status bar. Kept separate from build.py so the
core pipeline stays readable."""
from __future__ import annotations

import numpy as np

import html


def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


# --------------------------------------------------------------------- defs

def gradient_defs(pal):
    """SVG <defs> content: gradients used by the premium chrome."""
    return f"""
<linearGradient id="gFrame" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{pal["chrome"]}"/>
  <stop offset="0.5" stop-color="{pal["accent"]}"/>
  <stop offset="1" stop-color="{pal["portrait"]}"/>
</linearGradient>
<radialGradient id="gGlow" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="{pal["portrait"]}" stop-opacity="{pal["glow_op"]}"/>
  <stop offset="1" stop-color="{pal["portrait"]}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="gScan" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{pal["scan"]}" stop-opacity="0"/>
  <stop offset="0.5" stop-color="{pal["scan"]}" stop-opacity="{pal["scan_op"]}"/>
  <stop offset="1" stop-color="{pal["scan"]}" stop-opacity="0"/>
</linearGradient>
"""


# ------------------------------------------------------------------- pieces

def glow(pal, cx, cy, rx, ry):
    return (
        f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="url(#gGlow)"/>'
    )


def starfield(pal, n=150, w=1180, h=610, rng=None):
    """Subtle twinkling dots. Grouped by phase so the SVG stays small."""
    rng = rng or np.random.default_rng(7)
    xs = rng.uniform(20, w - 20, n)
    ys = rng.uniform(70, h - 20, n)
    rs = rng.uniform(0.6, 1.5, n)
    base = rng.uniform(0.08, 0.35, n)
    phase = rng.integers(0, 6, n)
    dur = rng.uniform(3.0, 5.5, n)
    out = []
    for p in range(6):
        sel = np.where(phase == p)[0]
        if len(sel) == 0:
            continue
        circles = "".join(
            f'<circle cx="{xs[i]:.0f}" cy="{ys[i]:.0f}" r="{rs[i]:.2f}" fill="{pal["star"]}" '
            f'opacity="{base[i]:.2f}">'
            f'<animate attributeName="opacity" dur="{dur[i]:.2f}s" repeatCount="indefinite" '
            f'values="{base[i]:.2f};{min(base[i] + 0.45, 0.85):.2f};{base[i]:.2f}"/>'
            f"</circle>"
            for i in sel
        )
        out.append(f'<g begin="{p * 0.17:.2f}s">{circles}</g>')
    return "".join(out)


def scanline(pal, w=1180, h=610):
    """A soft highlight band sweeping left -> right every ~9s."""
    bw = 260
    return (
        f'<rect x="-{bw}" y="70" width="{bw}" height="{h - 84}" fill="url(#gScan)">'
        f'<animateTransform attributeName="transform" type="translate" additive="sum" '
        f'dur="9s" repeatCount="indefinite" values="0 0;{w + 2 * bw} 0"/>'
        f"</rect>"
    )


def live_ping(pal, cx, cy):
    """Expanding ping ring behind the LIVE dot."""
    return (
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="4.5" fill="none" stroke="{pal["live"]}" '
        f'stroke-width="1.5">'
        f'<animate attributeName="r" values="4.5;15" dur="1.6s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0.8;0" dur="1.6s" repeatCount="indefinite"/>'
        f"</circle>"
    )


def accent_sparkle(pal, n=14, w=1180, h=610, rng=None):
    """A few accent-colored motes drifting upward — subtle premium sparkle."""
    rng = rng or np.random.default_rng(11)
    xs = rng.uniform(40, w - 40, n)
    ys = rng.uniform(120, h - 80, n)
    rs = rng.uniform(1.0, 2.0, n)
    dur = rng.uniform(7.0, 11.0, n)
    out = []
    for i in range(n):
        dy = rng.uniform(25, 60)
        out.append(
            f'<circle cx="{xs[i]:.0f}" cy="{ys[i]:.0f}" r="{rs[i]:.2f}" fill="{pal["accent"]}" opacity="0">'
            f'<animate attributeName="opacity" dur="{dur[i]:.2f}s" repeatCount="indefinite" '
            f'values="0;0.5;0"/>'
            f'<animateTransform attributeName="transform" type="translate" additive="sum" '
            f'dur="{dur[i]:.2f}s" repeatCount="indefinite" values="0 0;0 {-dy:.0f}"/>'
            f"</circle>"
        )
    return "".join(out)


def status_bar(pal, font, w=1180, h=610):
    """Bottom bar: title, online dot, equalizer, version, blinking cursor."""
    y = h - 42
    bh = 36
    # left: prompt
    left = (
        f'<text x="22" y="{y + bh / 2 + 4:.0f}" font-size="13" fill="{pal["text"]}" font-family="{font}">'
        f'<tspan fill="{pal["chrome"]}">❯</tspan> profile.sh'
        f'<tspan fill="{pal["accent"]}"> --online</tspan></text>'
    )
    # online dot (pulses)
    dot_cx, dot_cy = 236, y + bh / 2
    dot = (
        f'<circle cx="{dot_cx}" cy="{dot_cy:.0f}" r="3.5" fill="{pal["accent"]}">'
        f'<animate attributeName="opacity" values="1;0.3;1" keyTimes="0;0.5;1" dur="1.8s" repeatCount="indefinite"/>'
        f"</circle>"
    )
    # right: equalizer bars
    eq_x = w - 208
    eq_bot = y + bh - 12
    eq = []
    for i in range(4):
        hh = "10;22;14;20;8" if i % 2 == 0 else "20;10;24;12;16"
        eq.append(
            f'<rect x="{eq_x + i * 9}" y="{eq_bot - 22}" width="5" fill="{pal["chrome"]}">'
            f'<animate attributeName="height" dur="0.9s" repeatCount="indefinite" '
            f'begin="{i * 0.11:.2f}s" values="{hh}" keyTimes="0;0.2;0.4;0.6;0.8;1"/>'
            f'<animate attributeName="y" dur="0.9s" repeatCount="indefinite" '
            f'begin="{i * 0.11:.2f}s" values="{";".join(f"{eq_bot - int(v)}" for v in hh.split(";"))}" '
            f'keyTimes="0;0.2;0.4;0.6;0.8;1"/>'
            f"</rect>"
        )
    eq = "".join(eq)
    # version + cursor
    right = (
        f'<text x="{w - 168}" y="{y + bh / 2 + 4:.0f}" font-size="12" fill="{pal["dim"]}" font-family="{font}">'
        f'v2.1.0</text>'
        f'<rect x="{w - 40}" y="{y + bh / 2 - 8:.0f}" width="9" height="16" fill="{pal["accent"]}">'
        f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" dur="1.1s" repeatCount="indefinite"/>'
        f"</rect>"
    )
    return (
        f'<rect x="6" y="{y}" width="{w - 12}" height="{bh}" rx="10" fill="{pal["panel"]}" '
        f'stroke="{pal["outline"]}" stroke-width="1"/>'
        f'{left}{dot}{eq}{right}'
    )