# Deploy on Vercel (public link, no Streamlit changes)

The **Streamlit** dashboard (`src/dashboard/app.py`) stays as-is for Streamlit Cloud / Render.

This adds a **static React site** in `frontend/` for Vercel — same 7 tabs, same V2 data.

## One-time setup

1. Export latest JSON (from repo root):

```bash
python scripts/export_dashboard_json.py
```

2. Push to GitHub (includes `frontend/` and `frontend/public/data/*.json`).

3. [vercel.com](https://vercel.com) → **New Project** → import  
   `https://github.com/LinLyra/fifa-world-cup-2026-prediction-system`

4. **Root Directory:** `frontend`  
   **Build Command:** `npm run build`  
   **Output Directory:** `dist`

5. Deploy → share the `*.vercel.app` URL.

## Update data after pipeline runs

```bash
python scripts/export_dashboard_json.py
git add frontend/public/data/
git commit -m "Refresh dashboard JSON for Vercel"
git push
```

Vercel redeploys automatically on push.

## Visitor analytics (Vercel Web Analytics)

Code is already wired (`@vercel/analytics` in `frontend/src/main.tsx`).

1. Vercel Dashboard → your project → **Analytics** → **Enable** Web Analytics.
2. Redeploy (or push any commit) so production picks up the package.
3. Open your live `*.vercel.app` URL once (disable ad blockers for testing).
4. View **Visitors**, **Pageviews**, and custom event **`dashboard_tab`** (which tab users click) in the Analytics tab.

Local `npm run dev` does not send analytics — only the Vercel production deployment does.

## Comparison

| Host | App | GitHub icon | China access |
|------|-----|-------------|--------------|
| Streamlit Cloud | Python Streamlit | Yes | Often slow/blocked |
| Render | Python Streamlit | No | Often slow/blocked |
| **Vercel** | Static React | No | Sometimes works (not guaranteed) |
