# FIFA World Cup 2026 — Vercel Dashboard (React)

Static React dashboard with the **same 7 tabs** as the Streamlit app. Data is pre-exported JSON (no Python runtime on Vercel).

## Local dev

```bash
# From repo root — refresh JSON from latest CSVs
python scripts/export_dashboard_json.py

cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Deploy to Vercel (GitHub)

1. Push this repo to GitHub (includes `frontend/public/data/*.json`).
2. Go to [vercel.com](https://vercel.com) → **Add New Project** → import your GitHub repo.
3. Set **Root Directory** = `frontend`
4. Framework preset: **Vite** (auto-detected)
5. Deploy → you get a public `*.vercel.app` URL

No environment variables required. Streamlit deployment is unchanged (`src/dashboard/app.py`).

## Tabs

| Tab | Data file |
|-----|-----------|
| Champion | `champions.json` |
| Groups | `groups.json` |
| Bracket | `bracket_consensus.json`, `reach_probs.json` |
| Path Difficulty | `path_difficulty.json` |
| Matchups | `match_matrix.json`, `final_match_intel.json` |
| Power Rankings | `intelligence.json` |
| Behind the Forecast | static copy |

After model updates, re-run `python scripts/export_dashboard_json.py` and redeploy.
