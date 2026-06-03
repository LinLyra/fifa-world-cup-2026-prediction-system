"""
Optional public-dashboard analytics (no extra dependencies beyond requests).

Configure via Streamlit secrets or environment variables:
  PLAUSIBLE_DOMAIN          — e.g. forecast.yourdomain.com (Plausible dashboard)
  GA_MEASUREMENT_ID         — e.g. G-XXXXXXXXXX (Google Analytics)
  VISIT_WEBHOOK_URL         — POST JSON on each new browser session (Supabase, n8n, etc.)
  VISIT_LOG_FILE            — append JSON lines locally (self-hosted VPS)

Streamlit Community Cloud also shows viewer stats in the app admin UI (no code needed).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

import streamlit as st


def _config(key: str) -> str | None:
    try:
        val = st.secrets.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    except Exception:
        pass
    val = os.environ.get(key)
    return str(val).strip() if val else None


def _inject_html(snippet: str) -> None:
    st.components.v1.html(snippet, height=0, width=0)


def _plausible_snippet(domain: str) -> str:
    return (
        f'<script defer data-domain="{domain}" '
        f'src="https://plausible.io/js/script.js"></script>'
    )


def _ga_snippet(measurement_id: str) -> str:
    return f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{measurement_id}');
</script>
"""


def _post_webhook(url: str, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=3) as resp:
        resp.read()


def _append_local_log(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def setup_public_analytics() -> None:
    """Run once per Streamlit browser session."""
    if st.session_state.get("_analytics_initialized"):
        return
    st.session_state["_analytics_initialized"] = True

    plausible = _config("PLAUSIBLE_DOMAIN")
    if plausible:
        _inject_html(_plausible_snippet(plausible))

    ga_id = _config("GA_MEASUREMENT_ID")
    if ga_id:
        _inject_html(_ga_snippet(ga_id))

    payload = {
        "event": "dashboard_session",
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    webhook = _config("VISIT_WEBHOOK_URL")
    if webhook:
        try:
            _post_webhook(webhook, payload)
        except (error.URLError, TimeoutError, OSError):
            pass

    log_file = _config("VISIT_LOG_FILE")
    if log_file:
        try:
            _append_local_log(Path(log_file), payload)
        except OSError:
            pass
