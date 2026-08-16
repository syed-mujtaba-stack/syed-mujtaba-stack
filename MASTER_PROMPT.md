# GitHub Profile — Master Prompt + Step-by-Step Build Guide

This file contains everything you need to recreate **the exact same animated GitHub profile**
(photo → dithered SVG banner, dark/light themes, self-hosted stats cards, snake animation,
badges, featured projects, dev quote).

Two ways to use it:

1. **Give the MASTER PROMPT below to any AI agent** (Claude, opencode, ChatGPT, etc.) together
   with your profile details, and let the agent build it from scratch.
2. **Or follow the STEP-BY-STEP GUIDE** yourself.

---

## What You Will Get

- Animated **dark/light banner** (`dark.svg` + `light.svg`) built from YOUR photo as thousands of dots
- **Divider** SVGs matching your theme
- **Self-hosted GitHub stats** cards (your own Vercel instance — no public limits)
- **Contribution streak** card + **activity graph**
- Animated **contribution snake** (auto-updates daily via GitHub Actions)
- ~130 **Languages & Tools** badges grouped by category
- **Featured Projects** repo cards
- **Random dev quote** + fun facts section

---

## Prerequisites

| Item | Why | Where |
|---|---|---|
| GitHub account | Hosts the profile repo | github.com |
| Git installed | Push/pull | https://git-scm.com |
| Python 3.11+ | Builds the SVG banners | https://python.org |
| Node.js 20+ | GitHub Actions workflow | https://nodejs.org |
| Vercel account (CLI) | Self-host the stats service | https://vercel.com |
| A personal photo | Becomes the banner portrait (portrait orientation best) | — |

---

# ⭐ MASTER PROMPT

> Copy everything between the `---` markers. Replace the `[...]` placeholders with your details
> before handing it to the agent.

```
You are an expert GitHub profile designer. Build me a complete, production-ready GitHub profile
repository from scratch, matching the spec below. Work autonomously: scaffold files, write
scripts, generate assets, verify everything, and give me push commands at the end.

== MY PROFILE DETAILS ==
- GitHub username: [YOUR_USERNAME]
- Display name: [YOUR_NAME]
- Email (for git commits): [YOUR_EMAIL]
- Title / roles: [e.g. Full-Stack Developer · Agentic AI Developer · DevOps]
- Location: [CITY, COUNTRY]
- Education: [DEGREE]
- Current focus: [one line]
- Toolchain: [tools you use]
- LinkedIn: [full URL]
- Other socials: [Instagram/Facebook/X URLs]
- Portfolio site: [URL]
- Tech stack: [list everything you actually use]
- Photo: I will provide [photo.jpg]. Design the banner around it.

== BRANDING (use exactly these colors) ==
- Dark theme:  bg=#0A101F  portrait=#A78BFA  cyan=#22D3EE  green=#10B981
- Light theme: bg=#F4F6FB  portrait=#7C3AED  cyan=#0891B2  green=#10B981
- Text dark=#CBD5E1  text light=#334155  border=#1E293B
- Timeline: 19.5 seconds loop

== DELIVERABLES ==
1. Animated SVG banner pair (dark.svg + light.svg):
   - Dithered/stippled portrait of my photo inside a rounded terminal-style frame on the left,
     animated dots + SMIL <animate> (dots materialize, drift, glow, hue shift).
   - On the right: animated info panel (name, roles, contact line) and tech logos that morph
     between the portrait and the logo grid.
   - Same layout in both files, only colors differ. Use <picture> media query in README so
     GitHub auto-switches on theme.
   - Portrait must be CROPPED head-and-shoulders and CENTERED in the frame (check centroid).
2. Divider SVG pair (divider-dark.svg + divider-light.svg) matching the theme.
3. README.md (premium, dark/light aware) with these sections in order:
   - Banner + typing line
   - About Me
   - Currently Working On (+ collapsible "Now Learning")
   - Languages & Tools (~130 badges grouped: Languages / Frontend / Backend / Mobile /
     Databases / Cloud & DevOps / AI-ML / Tools & IDEs)
   - GitHub Stats + Streak + Activity Graph
   - Featured Projects (repo pin cards for [your 4-6 repos])
   - Random Dev Quote (quotes-github-readme)
   - Contribution Snake (animated)
   - More About Me
   - Connect With Me + visitor badge
4. GitHub Actions workflow (github-contribution-grid-snake) that renders the snake daily
   and pushes SVGs to the output branch.
5. Verification: run every image URL, confirm 200s; validate both SVGs parse and SMIL animates;
   check portrait centered in frame; confirm no broken badges.

== CONSTRAINTS ==
- No comments in code unless necessary. Clean, consistent style.
- Self-host the stats cards on Vercel (github-readme-stats fork) with a PAT secret; use your
  OWN instance URL in the README, never the public one.
- Do NOT use github-profile-trophy (public endpoint is broken / 402).
- If any badge logo slug 404s, fix or remove it. Shields.io returns 403 without a browser
  User-Agent — retry with one.
- Communicate progress, then finish with the exact git push commands.

Build it now, step by step, and verify each artifact before moving on.
```

---

# 🛠️ STEP-BY-STEP GUIDE

## Phase 0 — Scaffold

```bash
# Create the repo on github.com (public), then clone locally
git clone https://github.com/YOUR_USERNAME/YOUR_USERNAME.git
cd YOUR_USERNAME
git config user.name "Your Name"
git config user.email "you@email.com"
```

Create folders:

```
YOUR_USERNAME/
├── README.md
├── dark.svg / light.svg
├── divider-dark.svg / divider-light.svg
├── assets/photo/placeholder.jpg   ← YOUR photo here
├── scripts/
│   ├── build_banner.py            ← one-command banner builder
│   └── banner/
│       ├── portrait.py            ← photo → dot runs (crop, mask, threshold)
│       ├── build.py               ← layout constants + CROP
│       ├── verify.py              ← SVGs + metrics checks
│       └── ...
└── .github/workflows/
    └── contribution-snake.yml
```

## Phase 1 — Banner Scripts

Write the pipeline that turns `photo.jpg` into animated dot-art:

- `portrait.py` — load photo, crop to head-and-shoulders, convert to dithered dot runs.
  Key: a `subject_mask()` with `thr_scale` so the face is detected even in dark photos;
  and **light-mode adaptation**: if the photo's mean luminance < 115, the light-theme portrait
  must paint `(~ink) & mask` (the lit subject) instead of `ink`, or the face disappears.
- `build.py` — layout constants (`GRID_W`, frame box, `PXO/PYO`), the `CROP` tuple, band logic
  (`for b in range(int(band.max())+1)` — a cropped photo may fill fewer bands than the grid).
- `anim.py / logos.py / premium.py` — SMIL `<animate>` (materialize, drift, glow, hue), logo grid.
- `build_banner.py` — entry point: `python scripts/build_banner.py assets/photo/placeholder.jpg`
  → writes `dark.svg` + `light.svg`.
- `verify.py` — checks: SVG parses, SMIL OK, dots centered, band evenness, organic boundaries.

**Centering rule:** after building, compute the dot centroid vs. the frame center and adjust
`CROP` until centroid ≈ center.

## Phase 2 — Dividers

Generate two slim gradient divider SVGs (`divider-dark.svg`, `divider-light.svg`) with your
cyan→violet→green gradient. They sit between every README section.

## Phase 3 — Self-Hosted Stats (Vercel)

The public `github-readme-stats.vercel.app` rate-limits. Host your own:

```bash
# 1. Clone the stats service
git clone https://github.com/anuraghazra/github-readme-stats.git
cd github-readme-stats
npm install

# 2. Create a Personal Access Token (fine-grained, read-only) on GitHub:
#    Settings → Developer settings → Personal access tokens
#    Permissions: metadata:read (and public repos read).

# 3. Add the token to Vercel
vercel link                    # attach to a new project, e.g. "grs"
vercel env add PAT_1 production   # paste token
vercel deploy --prod

# 4. You now have https://grs-XXXX.vercel.app — THIS is the base URL
```

Verify: `https://grs-XXXX.vercel.app/api?username=YOUR_USERNAME` returns your real stats.
**Important:** the token must be on the SAME project your deploy went to — check the Vercel
project dashboard if cards say "Something went wrong".

## Phase 4 — Snake Workflow

Create `.github/workflows/contribution-snake.yml`:

- Trigger: `schedule` daily + `push` to main.
- Uses `Platane/snk@v3`, runs on the latest commit, `github_token: ${{ secrets.GITHUB_TOKEN }}`.
- Outputs `github-contribution-grid-snake.svg` + `-dark.svg` to the `output` branch.

Then in Settings → Pages, publish the `output` branch (or just use the `raw.githubusercontent`
URLs in the README — no Pages needed).

## Phase 5 — README Assembly

Assemble sections from the master-prompt deliverable list. Rules:

- Use `<picture><source media="(prefers-color-scheme: dark|light)" srcset=...>` for every
  themed image (banner, dividers).
- Stats/streak/graph cards: `bg_color=0A101F&title_color=22D3EE&icon_color=10B981&text_color=CBD5E1&border_color=1E293B` (dark) — the two modes via `<picture>` too if you want them theme-aware.
- Featured Projects use the **self-hosted** pin endpoint:
  `https://grs-XXXX.vercel.app/api/pin?username=YOU&repo=REPO&...`
- Quote: `https://quotes-github-readme.vercel.app/api?type=horizontal&theme=radical`

## Phase 6 — Verify Everything

1. **Every image URL returns 200** (use curl / a script with a browser User-Agent).
2. **SVG check:** parse both files; confirm `<animate>`/`<animateTransform>` exist.
3. **Centering:** dot centroid ≈ frame center in both themes.
4. **Visual:** open preview PNGs (render SVG → screenshot via headless Chrome) and eyeball them.
5. Commit + push, then hard-refresh your profile (Ctrl+F5).

---

# 🎨 Quick Customization

| Thing | Where to change |
|---|---|
| Photo | Replace `assets/photo/placeholder.jpg`, re-run `build_banner.py`, adjust `CROP` |
| Colors | `build.py` constants + README card params |
| Roles / typing lines | README typing-svg lines + banner text |
| Featured repos | README `/api/pin?repo=...` entries |
| Languages & Tools | README badge groups |
| Snake speed/colors | workflow + snake service options |

---

# 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| Stats card: "Something went wrong" | PAT missing on the **deployed project** in Vercel |
| Badge shows 403 / missing logo | Retry with browser User-Agent; replace the slug |
| Face not visible in light theme | Photo too dark → light-mode paints `~ink & mask` automatically |
| Portrait off-center | Shift `CROP` (x) until dot centroid ≈ frame center |
| Snake not updating | Check Actions ran; `output` branch has SVGs; README uses raw URLs |
| Trophy card broken | Known upstream issue — drop it |
