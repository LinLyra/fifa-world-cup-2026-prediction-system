# Public deploy + visitor analytics

Give classmates / judges a **URL** and see **how many people opened** the dashboard.

You do **not** need a public GitHub repo. You **do** need a host that runs Streamlit (or static files for React only).

---

## Recommended: Streamlit Community Cloud (easiest public link)

1. Push code to GitHub (**private repo is OK** on Streamlit Team; **free tier needs public repo**).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Main file: `src/dashboard/app.py`
4. Upload `data/` (or use Git LFS for large CSVs: `world_cup_brackets_v1.csv`, `match_strength_matrix_v2.csv`).
5. **Built-in analytics:** Streamlit Cloud → your app → **Analytics** (unique viewers over time). No extra code.

Secrets (Settings → Secrets) — optional Plausible / GA:

```toml
PLAUSIBLE_DOMAIN = "yourname-worldcup.streamlit.app"
```

---

## Option A — Plausible (simple dashboard, good for demos)

1. Sign up at [plausible.io](https://plausible.io) (trial / self-hosted).
2. Add your site domain (e.g. `xxx.streamlit.app`).
3. In Streamlit Cloud secrets or `.streamlit/secrets.toml`:

```toml
PLAUSIBLE_DOMAIN = "xxx.streamlit.app"
```

4. Redeploy. Open Plausible → **Visitors**, **Pageviews**.

The dashboard loads `src/dashboard/analytics.py` automatically when this variable is set.

---

## Option B — Google Analytics 4

```toml
GA_MEASUREMENT_ID = "G-XXXXXXXXXX"
```

View traffic in GA4 → Reports → Realtime / Acquisition.

---

## Option C — Your own “backend” (webhook per visit)

Use any endpoint that accepts `POST` JSON. Each **new browser session** sends:

```json
{"event": "dashboard_session", "ts": "2026-06-03T12:00:00+00:00"}
```

**Streamlit secret:**

```toml
VISIT_WEBHOOK_URL = "https://YOUR_BACKEND/visit"
```

**Examples:**

| Backend | Effort |
|---------|--------|
| [Supabase](https://supabase.com) table + Edge Function | Medium, free tier |
| [n8n](https://n8n.io) webhook → Google Sheet | Low |
| Small FastAPI on Railway/Fly.io | Medium |

---

## Option D — VPS self-host + local visit log (no third party)

On your server:

```bash
export VISIT_LOG_FILE="/var/log/worldcup_visits.jsonl"
streamlit run src/dashboard/app.py --server.port 8501
```

Count sessions:

```bash
wc -l /var/log/worldcup_visits.jsonl
```

---

## What to ship (data bundle)

```bash
python scripts/prepare_site_deploy.py
```

Upload **`data/`** (or contents of `site_deploy/streamlit_data/` into the right paths) with the app.

---

## Quick comparison

| Method | Public URL | Visitor stats | Private GitHub |
|--------|------------|---------------|----------------|
| Streamlit Cloud + built-in Analytics | Yes | Yes (Cloud UI) | Team / paid |
| Streamlit Cloud + Plausible | Yes | Yes (Plausible) | Team / paid |
| VPS + `VISIT_LOG_FILE` | Yes | Yes (line count) | N/A |
| Local only (`streamlit run`) | No | No | N/A |

---

## Local test analytics

```bash
export PLAUSIBLE_DOMAIN="localhost"
streamlit run src/dashboard/app.py
```

Or test webhook with [webhook.site](https://webhook.site) → paste URL into `VISIT_WEBHOOK_URL`.
