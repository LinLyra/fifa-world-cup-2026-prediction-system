"""
FIFA World Cup 2026 Forecast Engine — Public Dashboard
Reads pre-computed model outputs; does not retrain anything.
Run: streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bracket_tree as _bracket_tree_mod

importlib.reload(_bracket_tree_mod)
from analytics import setup_public_analytics  # noqa: E402
from bracket_tree import (  # noqa: E402
    build_most_likely_path,
    compute_reach_probs,
    render_bracket_svg,
    trace_team_path,
)

DATA = {
    "champion": ROOT / "data/predictions/world_cup_champion_probabilities_v2.csv",
    "groups": ROOT / "data/predictions/group_stage_simulation_v3_summary.csv",
    "intelligence": ROOT / "data/features/team_intelligence_v2.csv",
    "matchups": ROOT / "data/predictions/match_strength_matrix_v2.csv",
    "final_intel": ROOT / "data/intelligence/final_match_intelligence_v1.csv",
    "brackets": ROOT / "data/predictions/world_cup_brackets_v1.csv",
    "path_difficulty": ROOT / "data/predictions/path_difficulty_v1.csv",
    "fixtures": ROOT / "data/raw/group_fixtures_final.csv",
}

SIMULATIONS = 20_000
HISTORICAL_MATCHES = "49,000+"
CHAMPION_MIN_PROB = 0.002  # 0.2%
CHAMPION_TOP_N = 15
PATH_TABLE_TOP_N = 15

COLORS = {
    "pitch": "#1B5E20",
    "pitch_light": "#2E7D32",
    "gold": "#C9A227",
    "bg": "#F7F9F8",
    "card": "#FFFFFF",
    "text": "#111111",
    "muted": "#333333",
    "draw": "#78909C",
    "away": "#1565C0",
}

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, Segoe UI, sans-serif", color="#111111", size=13),
    title_font=dict(color="#111111"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=55, b=20),
)

AXIS_STYLE = dict(tickfont=dict(color="#111111"), title_font=dict(color="#111111"))


def apply_plotly_layout(fig: go.Figure, **kwargs) -> go.Figure:
    xaxis = {**AXIS_STYLE, **kwargs.pop("xaxis", {})}
    yaxis = {**AXIS_STYLE, **kwargs.pop("yaxis", {})}
    margin = {**PLOTLY_LAYOUT.get("margin", {}), **kwargs.pop("margin", {})}
    layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k != "margin"}
    fig.update_layout(**layout, margin=margin, xaxis=xaxis, yaxis=yaxis, **kwargs)
    return fig


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(180deg, {COLORS["bg"]} 0%, #EEF2EF 100%);
        }}
        .hero-banner {{
            background: linear-gradient(135deg, {COLORS["pitch"]} 0%, {COLORS["pitch_light"]} 55%, #388E3C 100%);
            border-radius: 16px;
            padding: 2rem 2.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(27, 94, 32, 0.25);
        }}
        .hero-head {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 8px 24px;
            margin-bottom: 0.5rem;
        }}
        .hero-banner h1 {{
            color: white !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            margin: 0 !important;
            letter-spacing: -0.02em;
            flex: 1 1 auto;
        }}
        .hero-banner p {{
            color: rgba(255,255,255,0.92);
            font-size: 1.05rem;
            line-height: 1.6;
            margin: 0;
        }}
        .hero-byline {{
            flex-shrink: 0;
            color: rgba(255,255,255,0.88);
            font-size: 0.95rem;
            white-space: nowrap;
        }}
        .hero-signature {{
            font-family: "Brush Script MT", "Segoe Script", "Snell Roundhand", "Apple Chancery", cursive;
            font-size: 1.45rem;
            font-style: italic;
            letter-spacing: 0.02em;
        }}
        .metric-card {{
            background: {COLORS["card"]};
            border: 1px solid #E0E8E3;
            border-left: 4px solid {COLORS["gold"]};
            border-radius: 12px;
            padding: 1.1rem 1.25rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            height: 100%;
            min-height: 96px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .metric-card .label {{
            color: #333333;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
        }}
        .metric-card .value {{
            color: #111111;
            font-size: 1.35rem;
            font-weight: 800;
            margin-top: 0.35rem;
            line-height: 1.25;
        }}
        .section-title {{
            color: #111111;
            font-size: 1.35rem;
            font-weight: 700;
            border-bottom: 3px solid {COLORS["gold"]};
            padding-bottom: 0.35rem;
            margin: 1.5rem 0 0.35rem 0;
        }}
        .section-tagline {{
            color: #555555;
            font-size: 0.95rem;
            margin: 0 0 1rem 0;
            font-style: italic;
        }}
        .method-box {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #E0E8E3;
            line-height: 1.75;
            color: #111111;
        }}
        .method-box h3 {{
            color: {COLORS["pitch"]};
            margin-top: 1.25rem;
            margin-bottom: 0.5rem;
            font-size: 1.05rem;
        }}
        .method-box h3:first-child {{
            margin-top: 0;
        }}
        .footer-note {{
            text-align: center;
            color: #333333;
            font-size: 0.9rem;
            padding: 1.5rem;
            border-top: 1px solid #E0E8E3;
            margin-top: 2rem;
        }}
        .dashboard-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
            margin: 0.25rem 0 1rem 0;
        }}
        .dashboard-table th,
        .dashboard-table td {{
            padding: 16px 14px;
            text-align: left;
            vertical-align: middle;
            border-bottom: 1px solid #E0E8E3;
            color: #111111;
        }}
        .dashboard-table th {{
            background: #F7F9F8;
            font-weight: 600;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .dashboard-table tr:hover td {{
            background: #F7F9F8;
        }}
        div[data-testid="stMetric"] {{
            background: white;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            border: 1px solid #E0E8E3;
        }}
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            color: #111111;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: #111111 !important;
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS["pitch"]} !important;
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, tagline: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="section-tagline">{tagline}</p>', unsafe_allow_html=True)


def data_fingerprint() -> str:
    """Invalidate Streamlit cache when any upstream CSV changes."""
    parts = []
    for key in sorted(DATA):
        path = DATA[key]
        parts.append(f"{key}:{path.stat().st_mtime_ns if path.exists() else 0}")
    return "|".join(parts)


@st.cache_data(show_spinner=False)
def load_csv(key: str, _fp: str) -> pd.DataFrame | None:
    path = DATA[key]
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def warn_missing(key: str, label: str) -> None:
    path = DATA[key]
    st.warning(
        f"**{label}** not found. Re-run the upstream pipeline to generate "
        f"`{path.relative_to(ROOT)}`."
    )


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"


def path_difficulty_label(percentile: float) -> tuple[str, str]:
    """Return (star rating, Easy/Medium/Hard) from path difficulty percentile."""
    if pd.isna(percentile):
        return "—", "—"
    p = float(percentile)
    if p >= 0.75:
        return "★★★★★", "Hard"
    if p >= 0.55:
        return "★★★★☆", "Hard"
    if p >= 0.35:
        return "★★★☆☆", "Medium"
    if p >= 0.15:
        return "★★☆☆☆", "Easy"
    return "★☆☆☆☆", "Easy"


def champion_prob_column(
    path_df: pd.DataFrame, champion_df: pd.DataFrame | None
) -> pd.DataFrame:
    out = path_df.copy()
    if "champion_prob_y" in out.columns:
        y = pd.to_numeric(out["champion_prob_y"], errors="coerce")
        if "champion_prob" in out.columns:
            out["champion_prob"] = pd.to_numeric(out["champion_prob"], errors="coerce").fillna(y)
        else:
            out["champion_prob"] = y
    elif "champion_prob_x" in out.columns and "champion_prob" not in out.columns:
        out["champion_prob"] = pd.to_numeric(out["champion_prob_x"], errors="coerce")

    if champion_df is not None and "champion_prob" in champion_df.columns:
        by_team = champion_df.set_index("team")["champion_prob"]
        if "champion_prob" in out.columns:
            out["champion_prob"] = pd.to_numeric(out["champion_prob"], errors="coerce")
            out["champion_prob"] = out["champion_prob"].fillna(out["team"].map(by_team))
        else:
            out["champion_prob"] = out["team"].map(by_team)

    if "champion_prob" in out.columns:
        out["champion_prob"] = pd.to_numeric(out["champion_prob"], errors="coerce")

    drop = [c for c in out.columns if c.startswith("champion_prob_")]
    return out.drop(columns=drop, errors="ignore")


def render_html_table(df: pd.DataFrame, table_class: str = "dashboard-table") -> None:
    header = "".join(f"<th>{col}</th>" for col in df.columns)
    body_rows = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{row[col]}</td>" for col in df.columns)
        body_rows.append(f"<tr>{cells}</tr>")
    st.markdown(
        f'<table class="{table_class}"><thead><tr>{header}</tr></thead>'
        f"<tbody>{''.join(body_rows)}</tbody></table>",
        unsafe_allow_html=True,
    )


def format_market_value(eur: float) -> str:
    if pd.isna(eur):
        return "—"
    if eur >= 1_000_000_000:
        return f"€{eur / 1_000_000_000:.2f}B"
    if eur >= 1_000_000:
        return f"€{eur / 1_000_000:.0f}M"
    return f"€{eur:,.0f}"


def parse_scorelines(raw: str) -> list[tuple[str, float]]:
    if not isinstance(raw, str) or not raw.strip():
        return []
    out = []
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        match = re.match(r"([^:]+):([\d.]+)", part)
        if match:
            out.append((match.group(1).strip(), float(match.group(2))))
    return out


def horizontal_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str,
    text_digits: int = 1,
) -> go.Figure:
    plot_df = df.sort_values(x, ascending=True)
    fig = px.bar(
        plot_df,
        x=x,
        y=y,
        orientation="h",
        title=title,
        text=plot_df[x].apply(lambda v: pct(v, text_digits)),
        color_discrete_sequence=[color],
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    apply_plotly_layout(
        fig,
        height=max(420, len(plot_df) * 28),
        xaxis=dict(tickformat=".0%", title="Probability"),
        yaxis=dict(title=""),
        showlegend=False,
    )
    return fig


def model_confidence(
    team_a: str,
    team_b: str,
    row: pd.Series,
    intel: pd.DataFrame | None,
    fin: pd.Series | None,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    score = 0

    hw, dr, aw = float(row["home_win_prob"]), float(row["draw_prob"]), float(row["away_win_prob"])
    favourite_margin = max(hw, dr, aw) - sorted([hw, dr, aw])[-2]

    if intel is not None and "team" in intel.columns:
        ia = intel[intel["team"] == team_a]
        ib = intel[intel["team"] == team_b]
        if not ia.empty and not ib.empty and "elo" in intel.columns:
            elo_gap = abs(float(ia.iloc[0]["elo"]) - float(ib.iloc[0]["elo"]))
            if elo_gap >= 120:
                reasons.append("Large Elo gap between teams")
                score += 2
            elif elo_gap >= 60:
                reasons.append("Moderate strength separation")
                score += 1
            else:
                reasons.append("Teams closely matched on Elo")

        if not ia.empty and not ib.empty and "market_champion_prob" in intel.columns:
            ma = float(ia.iloc[0]["market_champion_prob"])
            mb = float(ib.iloc[0]["market_champion_prob"])
            model_fav = team_a if hw >= aw else team_b
            market_fav = team_a if ma >= mb else team_b
            if model_fav == market_fav:
                reasons.append("Market sentiment aligns with model favourite")
                score += 1

    if favourite_margin >= 0.22:
        reasons.append("Clear favourite in win probabilities")
        score += 1
    elif favourite_margin >= 0.12:
        reasons.append("Moderate edge in win probabilities")
    else:
        reasons.append("Toss-up — outcome probabilities are tight")
        score -= 1

    if fin is not None:
        adj = sum(
            abs(float(fin.get(k, 0) or 0))
            for k in ("injury_effect", "squad_effect", "upset_effect", "odds_effect")
        )
        if adj < 0.08:
            reasons.append("No major pre-match intelligence adjustment")
            score += 1
        else:
            reasons.append("Pre-match intelligence layer applied — wider uncertainty")
            score -= 1
    else:
        reasons.append("Base model probabilities (no live match intelligence row)")
        score += 0

    if score >= 3:
        level = "High"
    elif score >= 1:
        level = "Medium"
    else:
        level = "Low"

    return level, reasons


def render_hero(team_count: int | None) -> None:
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-head">
                <h1>⚽ FIFA World Cup 2026 Forecast Engine</h1>
                <span class="hero-byline">by: <span class="hero-signature">LLyra</span></span>
            </div>
            <p>Prediction Engine · Simulation Engine · Intelligence Layer — built on
            {HISTORICAL_MATCHES} international matches and {SIMULATIONS:,} full-tournament
            Monte Carlo simulations from group stage to final.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    metrics = [
        ("Simulations", f"{SIMULATIONS:,}"),
        ("Historical Matches", HISTORICAL_MATCHES),
        ("Teams Modeled", str(team_count) if team_count else "48"),
        ("Engine", "V2 Pre-Match Forecast"),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="label">{label}</div>'
                f'<div class="value">{value}</div></div>',
                unsafe_allow_html=True,
            )


def render_champion(df: pd.DataFrame | None) -> None:
    section("🏆 Who Wins the World Cup?", "Title probabilities from 20,000 full-tournament simulations.")
    if df is None:
        warn_missing("champion", "Champion probabilities")
        return

    pool = df[df["champion_prob"] >= CHAMPION_MIN_PROB].sort_values(
        "champion_prob", ascending=False
    )
    if pool.empty:
        pool = df.sort_values("champion_prob", ascending=False)
    contenders = pool.head(CHAMPION_TOP_N).copy()

    st.caption(
        f"Top {len(contenders)} title contenders (≥{pct(CHAMPION_MIN_PROB, 1)} shown when available). "
        f"Chart and table use the same ranking."
    )

    chart_height = max(380, len(contenders) * 32)
    table_height = chart_height + 40

    col_chart, col_table = st.columns([3, 2])
    with col_chart:
        fig = horizontal_bar(
            contenders,
            "champion_prob",
            "team",
            f"Top {len(contenders)} — Title Probability",
            COLORS["gold"],
            text_digits=2,
        )
        fig.update_layout(height=chart_height)
        st.plotly_chart(fig, use_container_width=True)
    with col_table:
        display = contenders[["team", "champion_prob", "titles"]].copy()
        display["champion_prob"] = display["champion_prob"].map(lambda x: pct(x, 2))
        display.columns = ["Team", "Title Prob", "Simulated Titles"]
        st.dataframe(display, hide_index=True, use_container_width=True, height=table_height)


@st.cache_data(show_spinner="Computing knockout reach rates…")
def get_reach_probs(brackets: pd.DataFrame, matchups: pd.DataFrame, _fp: str) -> pd.DataFrame:
    return compute_reach_probs(brackets, matchups)


def render_groups(df: pd.DataFrame | None) -> None:
    section("📊 Who Survives the Group Stage?", "Advance probabilities including best third-place routes.")
    if df is None:
        warn_missing("groups", "Group stage simulation summary")
        return

    ranked = df.sort_values("advance_prob", ascending=False).copy()
    top = ranked.head(15)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(name="Group Winner", x=top["team"], y=top["group_winner_prob"], marker_color=COLORS["pitch"])
    )
    fig.add_trace(
        go.Bar(name="Top 2", x=top["team"], y=top["group_top2_prob"], marker_color=COLORS["pitch_light"])
    )
    fig.add_trace(
        go.Bar(name="Advance", x=top["team"], y=top["advance_prob"], marker_color=COLORS["gold"])
    )
    apply_plotly_layout(
        fig,
        barmode="group",
        title="Top 15 Teams by Advance Probability",
        height=460,
        xaxis=dict(tickangle=-45, title=""),
        yaxis=dict(tickformat=".0%", title="Probability"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

    full = ranked[["team", "group_winner_prob", "group_top2_prob", "advance_prob"]].copy()
    for col in ["group_winner_prob", "group_top2_prob", "advance_prob"]:
        full[col] = full[col].map(lambda x: pct(x, 1))
    full.columns = ["Team", "Group Winner", "Top 2", "Advance"]
    st.markdown("#### Group Qualification — All Teams")
    st.dataframe(full, hide_index=True, use_container_width=True, height=520)


def render_power_rankings(df: pd.DataFrame | None) -> None:
    section(
        "💪 Power Rankings",
        "How strong is every team entering the tournament?",
    )
    if df is None:
        warn_missing("intelligence", "Team strength rankings")
        return

    top = df.nlargest(30, "intelligence_score_v2").copy()
    fig = px.scatter(
        top,
        x="attack_rating",
        y="defense_rating",
        size="intelligence_score_v2",
        color="intelligence_score_v2",
        hover_name="team",
        color_continuous_scale=["#E8F5E9", COLORS["pitch"], "#1B5E20"],
        title="Team Strength Landscape — Attack vs Defense",
        labels={"attack_rating": "Attack Rating", "defense_rating": "Defense Rating"},
    )
    apply_plotly_layout(fig, height=420, coloraxis_colorbar=dict(title="Strength"))
    st.plotly_chart(fig, use_container_width=True)

    table = top[
        [
            "team",
            "elo",
            "market_value_eur",
            "market_champion_prob",
            "intelligence_score_v2",
            "attack_rating",
            "defense_rating",
        ]
    ].copy()
    table["market_value_eur"] = table["market_value_eur"].map(format_market_value)
    table["market_champion_prob"] = table["market_champion_prob"].map(lambda x: pct(x, 1))
    table["intelligence_score_v2"] = table["intelligence_score_v2"].map(lambda x: f"{x:.3f}")
    table["elo"] = table["elo"].map(lambda x: f"{x:.0f}")
    table["attack_rating"] = table["attack_rating"].map(lambda x: f"{x:.2f}")
    table["defense_rating"] = table["defense_rating"].map(lambda x: f"{x:.2f}")
    table.columns = [
        "Team",
        "Elo",
        "Squad Value",
        "Market Title Prob",
        "Strength Score",
        "Attack",
        "Defense",
    ]
    st.dataframe(table, hide_index=True, use_container_width=True)


def wc_team_set(
    fixtures_df: pd.DataFrame | None,
    groups_df: pd.DataFrame | None = None,
    champion_df: pd.DataFrame | None = None,
) -> set[str] | None:
    if fixtures_df is not None:
        return set(fixtures_df["home_team"]).union(set(fixtures_df["away_team"]))
    if groups_df is not None and "team" in groups_df.columns:
        return set(groups_df["team"])
    if champion_df is not None and "team" in champion_df.columns:
        return set(champion_df["team"])
    return None


def render_matchup_explorer(
    matchups: pd.DataFrame | None,
    final_intel: pd.DataFrame | None,
    intel: pd.DataFrame | None,
    wc_teams: set[str] | None = None,
) -> None:
    section("⚔️ Matchup Explorer", "What happens if Team A plays Team B?")
    if matchups is None:
        warn_missing("matchups", "Match strength matrix")
        return

    teams = sorted(wc_teams) if wc_teams else sorted(
        set(matchups["home_team"]) | set(matchups["away_team"])
    )
    if intel is not None:
        ranked = intel.nlargest(48, "intelligence_score_v2")["team"].tolist()
        default_a = ranked[0]
        default_b = ranked[1] if len(ranked) > 1 else ranked[0]
    else:
        default_a, default_b = teams[0], teams[1]

    c1, c2 = st.columns(2)
    with c1:
        team_a = st.selectbox(
            "Team A (Home)",
            teams,
            index=teams.index(default_a) if default_a in teams else 0,
        )
    with c2:
        others = [t for t in teams if t != team_a]
        default_b_idx = others.index(default_b) if default_b in others else 0
        team_b = st.selectbox("Team B (Away)", others, index=default_b_idx)

    row = matchups[(matchups["home_team"] == team_a) & (matchups["away_team"] == team_b)]
    if row.empty:
        st.info(f"No pre-computed row for **{team_a}** vs **{team_b}** (home/away).")
        return

    r = row.iloc[0]
    fin = None
    if final_intel is not None:
        fi = final_intel[
            (final_intel["home_team"] == team_a) & (final_intel["away_team"] == team_b)
        ]
        if not fi.empty:
            fin = fi.iloc[0]

    level, reasons = model_confidence(team_a, team_b, r, intel, fin)

    conf_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(level, "⚪")
    st.markdown(
        f"**Model Confidence:** {conf_color} **{level}**  \n"
        + "  \n".join(f"- {x}" for x in reasons)
    )

    m1, m2, m3, m4 = st.columns(4)
    home_xg = float(fin["final_home_xg"]) if fin is not None else float(r["expected_home_goals"])
    away_xg = float(fin["final_away_xg"]) if fin is not None else float(r["expected_away_goals"])
    m1.metric(f"{team_a} xG", f"{home_xg:.2f}")
    m2.metric(f"{team_b} xG", f"{away_xg:.2f}")
    m3.metric("Most Likely Score", f"{int(r['pred_home_score'])}–{int(r['pred_away_score'])}")
    m4.metric("Scoreline Prob", pct(r["score_probability"], 1))

    left, right = st.columns(2)
    with left:
        outcomes = pd.DataFrame(
            {
                "Outcome": [f"{team_a} Win", "Draw", f"{team_b} Win"],
                "Probability": [r["home_win_prob"], r["draw_prob"], r["away_win_prob"]],
            }
        )
        fig = px.bar(
            outcomes,
            x="Outcome",
            y="Probability",
            text=outcomes["Probability"].map(lambda x: pct(x, 2)),
            color="Outcome",
            color_discrete_map={
                f"{team_a} Win": COLORS["pitch"],
                "Draw": COLORS["draw"],
                f"{team_b} Win": COLORS["away"],
            },
            title="Match Outcome Probabilities",
        )
        apply_plotly_layout(
            fig,
            height=400,
            showlegend=False,
            margin=dict(t=55, b=30, l=20, r=20),
            yaxis=dict(range=[0, 0.8], tickformat=".0%"),
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)
        total = r["home_win_prob"] + r["draw_prob"] + r["away_win_prob"]
        st.caption(f"Home + Draw + Away = {pct(total, 2)} · Y-axis capped at 80% for readability")

    with right:
        scorelines = parse_scorelines(r["top_5_scorelines"])
        if scorelines:
            sl_df = pd.DataFrame(scorelines, columns=["Scoreline", "Probability"])
            fig2 = horizontal_bar(sl_df, "Probability", "Scoreline", "Top 5 Scorelines", COLORS["gold"])
            apply_plotly_layout(fig2, height=400, margin=dict(t=55, b=20, l=80, r=30))
            fig2.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("Top scorelines unavailable for this matchup.")


def render_path_difficulty(path_df: pd.DataFrame | None, champion_df: pd.DataFrame | None) -> None:
    section(
        "🛤️ Path Difficulty",
        "How hard is each team's route to the trophy?",
    )
    render_path_difficulty_chart(path_df, champion_df)
    render_road_to_final(path_df, champion_df)


def render_path_difficulty_chart(
    path_df: pd.DataFrame | None,
    champion_df: pd.DataFrame | None,
) -> None:
    st.markdown("#### Path Difficulty vs Title Chance")
    st.caption(
        f"Higher path difficulty = tougher expected opponents on the knockout route. "
        f"Bubble size reflects title probability (same {SIMULATIONS:,} simulations as the Champion tab)."
    )
    if path_df is None:
        warn_missing("path_difficulty", "Path difficulty layer")
        return
    if "expected_path_difficulty" not in path_df.columns:
        st.caption("Path difficulty metrics unavailable.")
        return

    plot = champion_prob_column(path_df, champion_df)
    plot = plot.dropna(subset=["expected_path_difficulty"])
    if plot.empty:
        st.caption("No path difficulty rows to chart.")
        return

    scatter_kw: dict = dict(
        x="expected_path_difficulty",
        y="champion_prob",
        hover_name="team",
        title="Title Probability vs Expected Path Difficulty",
        labels={
            "expected_path_difficulty": "Path Difficulty",
            "champion_prob": "Title Probability",
        },
    )
    if plot["champion_prob"].notna().any():
        scatter_kw["size"] = "champion_prob"
    if "path_efficiency" in plot.columns and plot["path_efficiency"].notna().any():
        scatter_kw["color"] = "path_efficiency"

    fig = px.scatter(plot, **scatter_kw)
    apply_plotly_layout(fig, height=380, margin=dict(t=55, b=30, l=50, r=20))
    st.plotly_chart(fig, use_container_width=True)


def render_road_to_final(
    path_df: pd.DataFrame | None,
    champion_df: pd.DataFrame | None,
) -> None:
    st.markdown("#### Road to the Final")
    st.caption("Expected opponent strength on the most likely knockout path.")
    if path_df is None:
        warn_missing("path_difficulty", "Path difficulty layer")
        return

    plot = champion_prob_column(path_df, champion_df)
    plot = plot.sort_values("champion_prob", ascending=False, na_position="last")
    plot = plot[plot["champion_prob"] >= CHAMPION_MIN_PROB].head(PATH_TABLE_TOP_N)
    if plot.empty:
        plot = champion_prob_column(path_df, champion_df).nlargest(PATH_TABLE_TOP_N, "champion_prob")

    rows = []
    for rank, (_, row) in enumerate(plot.iterrows(), start=1):
        pctile = row.get("path_difficulty_percentile", float("nan"))
        stars, tier = path_difficulty_label(pctile)
        opp = row.get("expected_path_difficulty", float("nan"))
        cp = row.get("champion_prob", float("nan"))
        rows.append(
            {
                "Path Rank": rank,
                "Team": row["team"],
                "Title Prob": pct(cp, 1) if pd.notna(cp) else "—",
                "Expected Opponent Strength": f"{opp:.2f}" if pd.notna(opp) else "—",
                "Difficulty": tier,
                "Rating": stars,
            }
        )

    render_html_table(pd.DataFrame(rows))


def render_bracket_path_tree(
    brackets: pd.DataFrame | None,
    matchups: pd.DataFrame | None,
    champion_df: pd.DataFrame | None,
    path_df: pd.DataFrame | None,
    fixtures_df: pd.DataFrame | None = None,
    groups_df: pd.DataFrame | None = None,
) -> None:
    section(
        "🌳 Bracket",
        "Consensus knockout pathway from 20,000 full-tournament simulations.",
    )

    if brackets is None or matchups is None:
        if brackets is None:
            warn_missing("brackets", "Knockout brackets")
        if matchups is None:
            warn_missing("matchups", "Match strength matrix")
        return

    matches = build_most_likely_path(brackets, matchups)
    reach_df = get_reach_probs(brackets, matchups, data_fingerprint())
    champ_map = (
        champion_df.set_index("team")["champion_prob"].to_dict()
        if champion_df is not None
        else {}
    )
    path_map = (
        path_df.set_index("team")["expected_path_difficulty"].to_dict()
        if path_df is not None and "expected_path_difficulty" in path_df.columns
        else {}
    )

    teams = sorted({m.home for m in matches} | {m.away for m in matches} | {m.winner for m in matches})

    st.markdown("#### Consensus Knockout Bracket")
    st.info(
        "Round of 32 shows the **most frequent complete draw** across 20,000 simulations — not always the "
        "same teams as the highest **group winner %** on the Groups tab (e.g. Germany may be ~52% to win "
        "Group E while another team occupies the E winner slot in this draw). Expand **Groups A–L** below "
        "to map each letter to teams and this bracket."
    )
    st.markdown(
        """
        **Round of 32** = joint-modal draw (32 unique teams). **R16 → Final** = KO win % on that path.

        Tree percentages are **KO win %**, not group advance rates.
        """
    )
    st.caption("Select a team to highlight its projected route to the trophy.")

    active = st.selectbox(
        "Highlight team path",
        ["— Full consensus bracket —"] + teams,
        index=0,
    )
    active_team = None if active.startswith("—") else active

    if active_team:
        st.info(
            "Projected route on the **consensus bracket** — the most likely knockout path for this "
            "team if the modal draw and model win probabilities hold. Not a single simulated run "
            "or a guaranteed title path."
        )
        path_ids = trace_team_path(matches, active_team)
        if not path_ids:
            st.warning(
                f"**{active_team}** does not appear on the consensus Round of 32 draw."
            )
        else:
            if not reach_df.empty and active_team in reach_df["team"].values:
                r = reach_df[reach_df["team"] == active_team].iloc[0]
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.metric("Reach R32", pct(r["reach_r32"], 0))
                c2.metric("Reach R16", pct(r["reach_r16"], 0))
                c3.metric("Reach QF", pct(r["reach_qf"], 0))
                c4.metric("Reach SF", pct(r["reach_sf"], 0))
                c5.metric("Reach Final", pct(r["reach_final"], 0))
                c6.metric("Win World Cup", pct(r["reach_win"], 0))

        html = render_bracket_svg(
            matches,
            active_team,
            champ_map,
            path_map,
            path_ids,
            focus_only=True,
        )
        st.components.v1.html(html, height=340, scrolling=False)

        with st.expander("View full consensus bracket (all teams)"):
            full_html = render_bracket_svg(matches, None, champ_map, path_map, set(), focus_only=False)
            st.components.v1.html(full_html, height=680, scrolling=False)
    else:
        html = render_bracket_svg(matches, None, champ_map, path_map, set(), focus_only=False)
        st.components.v1.html(html, height=680, scrolling=False)

    final = [m for m in matches if m.match_id == 104]
    if final:
        f = final[0]
        st.caption(
            f"Consensus final pairing: **{f.home}** vs **{f.away}** "
            f"(model KO edge **{f.winner}** {max(f.p_home, f.p_away):.0%}). "
            f"See **Champion** tab for title probabilities."
        )

    if fixtures_df is not None and groups_df is not None:
        from group_reference import group_letter_reference_table

        st.markdown("---")
        st.markdown("#### Groups A–L and this Round of 32 draw")
        st.caption(
            "Win / Top 2 / Advance match the Groups tab. **This R32 draw** = consensus bracket only."
        )
        ref = group_letter_reference_table(fixtures_df, groups_df, matches)
        st.dataframe(ref, use_container_width=True, hide_index=True)


def render_behind_the_forecast() -> None:
    section("📐 Behind the Forecast", "How does the model work?")
    st.markdown(
        f"""
        <div class="method-box">
        <h3>{HISTORICAL_MATCHES} International Matches</h3>
        <p>The engine is trained on more than 49,000 historical international football matches
        spanning over a century of competition. This is the foundation for every team rating
        and probability on the dashboard.</p>

        <h3>Team Strength Modelling</h3>
        <p>Each national team is represented through a multi-layer strength profile built from
        historical performance, attacking output, defensive resilience, squad value, and market
        signals.</p>

        <h3>Probabilistic Match Forecasting</h3>
        <p>Match outcomes are generated with Poisson-based scoreline modelling and Dixon–Coles
        low-score correction, producing realistic expected goals, score distributions, and
        win/draw/loss probabilities.</p>

        <h3>Tournament Simulation</h3>
        <p>We run {SIMULATIONS:,} Monte Carlo simulations of the full FIFA World Cup 2026
        structure, from the group stage to the knockout rounds and final, to estimate
        advancement and title probabilities.</p>

        <h3>Pre-Match Intelligence</h3>
        <p>Before kickoff, the model can incorporate squad availability, tactical profile,
        betting market movement, and competitive context to refine match expectations.</p>

        <h3>Squad Availability Intelligence</h3>
        <p>Player absences, suspensions, and squad disruptions are tracked and translated into
        team-level adjustments, helping the model reflect real-world availability without
        exposing private pipeline details.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="FIFA World Cup 2026 Forecast Engine",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()
    setup_public_analytics()

    fp = data_fingerprint()
    champion_df = load_csv("champion", fp)
    groups_df = load_csv("groups", fp)
    intel_df = load_csv("intelligence", fp)
    matchups_df = load_csv("matchups", fp)
    final_intel_df = load_csv("final_intel", fp)
    brackets_df = load_csv("brackets", fp)
    path_df = load_csv("path_difficulty", fp)
    fixtures_df = load_csv("fixtures", fp)

    wc_teams = wc_team_set(fixtures_df, groups_df, champion_df)
    team_count = len(wc_teams) if wc_teams else (
        intel_df["team"].nunique() if intel_df is not None else None
    )

    render_hero(team_count)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "🏆 Champion",
            "📊 Groups",
            "🌳 Bracket",
            "🛤️ Path Difficulty",
            "⚔️ Matchups",
            "💪 Power Rankings",
            "📐 Behind the Forecast",
        ]
    )

    with tab1:
        render_champion(champion_df)

    with tab2:
        render_groups(groups_df)

    with tab3:
        render_bracket_path_tree(
            brackets_df,
            matchups_df,
            champion_df,
            path_df,
            fixtures_df,
            groups_df,
        )

    with tab4:
        render_path_difficulty(path_df, champion_df)

    with tab5:
        render_matchup_explorer(matchups_df, final_intel_df, intel_df, wc_teams)

    with tab6:
        render_power_rankings(intel_df)

    with tab7:
        render_behind_the_forecast()

    st.markdown(
        f"""
        <div class="footer-note">
        FIFA World Cup 2026 Forecast Engine — Prediction · Simulation · Intelligence<br>
        <span style="font-size:0.85rem;color:#555;">
        V2 Pre-Match Forecast · {SIMULATIONS:,} tournament simulations
        </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
