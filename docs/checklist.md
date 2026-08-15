# Upload & Go-Live Checklist

All automated work is done. These are the remaining manual steps (need your accounts/browser):

## 1. Real photo (recommended)
- Replace `assets/photo/placeholder.jpg` with your real head-and-shoulders photo
  (flat background, even lighting, ≥1000px short edge).
- Regenerate the banners: `python scripts/build_banner.py assets/photo/yourphoto.jpg`
- Commit + push the new `dark.svg` / `light.svg`.

## 2. Verify the banner
- Open `dark.svg` and `light.svg` in Chrome/Edge. Watch one full ~20s loop
  (portrait → 5 logos → repeats).
- DevTools → Rendering → *Emulate CSS prefers-color-scheme* to test the theme switch.

## 3. GitHub repo
- Repo `syed-mujtaba-stack/syed-mujtaba-stack` is created (public) and files are pushed by the agent.
- Settings → **Actions → General** → ensure *Allow all actions* (so the snake workflow can run).

## 4. Contribution snake
- **Actions** tab → "generate animation" → **Run workflow**.
- After it finishes, confirm `output` branch contains `github-contribution-grid-snake.svg`
  and `...-dark.svg`. The README snake section will then render.

## 5. Self-hosted stats (see `docs/stats.md` for full detail)
1. GitHub → Developer settings → PAT (classic) → scope `repo`, **no expiration**.
2. Fork `anuraghazra/github-readme-stats` → deploy on Vercel → env var `PAT_1` = token.
3. Copy your Vercel URL into `README.md` — it appears in the 2 stat-card links
   (replace `github-readme-stats.vercel.app`).
4. Optional: deploy `DenverCoder1/github-readme-streak-stats` for a reliable streak card.
   If you skip it, remove the streak `<img>` from the README.

## 6. Portfolio link
- When your portfolio goes live, add a badge/URL to the Connect section and update the
  banner's "portfolio: coming soon" info row (edit `SYSTEM.INFO` in `scripts/banner/build.py`).

## 7. Sanity pass
- Open your profile at `github.com/syed-mujtaba-stack/syed-mujtaba-stack` and confirm:
  banner plays, stats cards load, snake renders, badges link correctly.