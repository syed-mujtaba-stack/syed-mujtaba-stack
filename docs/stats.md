# Phase 2 — Self-hosted github-readme-stats

The profile uses the **self-hosted** stats service (the public `github-readme-stats.vercel.app`
instance is rate-limited and occasionally throttles profile views). One-time ~5 minute setup:

## 1. Create a GitHub token
1. github.com → Settings → Developer settings → **Personal access tokens → Tokens (classic)** → *Generate new token (classic)*.
2. Scopes: tick **repo** (full). Expiration: **No expiration** (Vercel reads it server-side; a 90-day
   token will silently break the cards later).
3. Name it e.g. `vercel-grs` and copy it. Keep it secret.

## 2. Deploy the stats service
1. Fork **anuraghazra/github-readme-stats** to your account (github.com/anuraghazra/github-readme-stats → Fork).
2. vercel.com → **Add New → Project** → import the fork.
3. In project settings → **Environment Variables** add:
   - `PAT_1` = the token from step 1 (repo scope, no expiry).
4. Deploy. You get a URL like `https://github-readme-stats-<hash>.vercel.app`.
   **Record this URL** — it goes into `README.md` in 3 places (stats, top-langs; streak is separate below).

> Keep the fork updated: fork → *Sync fork → Update branch* occasionally to pull upstream fixes.

## 3. Streak (optional, separate service)
The streak card is a different repo: **DenverCoder1/github-readme-streak-stats** — same deploy steps
(no token needed). The README currently uses the reliable public instance `streak-stats.demolab.com`
(the old herokuapp host is deprecated). Swap in your own Vercel URL if you self-host.

## 4. The card URLs (README-ready)

Replace `https://github-readme-stats.vercel.app` below with **your** Vercel URL.

```markdown
<p align="center">
  <img src="https://github-readme-stats.vercel.app/api?username=syed-mujtaba-stack&hide_rank=true&hide_border=true&bg_color=0A101F&title_color=22D3EE&icon_color=10B981&text_color=CBD5E1&border_color=1E293B" alt="GitHub Stats" width="49%" />
  <img src="https://github-readme-stats.vercel.app/api/top-langs?username=syed-mujtaba-stack&layout=compact&hide_border=true&bg_color=0A101F&title_color=22D3EE&icon_color=10B981&text_color=CBD5E1&border_color=1E293B" alt="Top Languages" width="49%" />
</p>
<p align="center">
  <img src="https://streak-stats.demolab.com/?user=syed-mujtaba-stack&hide_border=true&background=0A101F&stroke=22D3EE&ring=10B981&fire=10B981&currStreakNum=CBD5E1&sideNums=CBD5E1&currStreakLabel=22D3EE&sideLabels=22D3EE&dates=64748B" alt="GitHub Streak" width="100%" />
</p>
```

## Why `hide_rank=true`
The default rank badge is stars-weighted — new accounts get a misleadingly low rank. Hide it.

## Palette mapping
`bg=0A101F` background · `title=22D3EE` chrome cyan · `icon=10B981` accent green · `text=CBD5E1`
soft white · `border=1E293B` subtle border — mirrors the banner palette.