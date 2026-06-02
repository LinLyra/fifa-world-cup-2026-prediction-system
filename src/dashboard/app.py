"""
FIFA World Cup 2026 Forecast Engine V1 — Public Dashboard
Reads pre-computed model outputs; does not retrain anything.
Run: streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA = {
    "champion": ROOT / "data/predictions/world_cup_champion_probabilities_v2.csv",
    "groups": ROOT / "data/predictions/group_stage_simulation_v2.csv",
    "intelligence": ROOT / "data/features/team_intelligence_v2.csv",
    "matchups": ROOT / "data/predictions/match_strength_matrix_v2.csv",
    "brackets": ROOT / "data/predictions/world_cup_brackets_v1.csv",
}

SIMULATIONS = 20_000
HISTORICAL_MATCHES = "49,000+"
MODEL_VERSION = "V1 Base Forecast Engine"

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
    margin=dict(l=20, r=20, t=40, b=20),
)

AXIS_STYLE = dict(tickfont=dict(color="#111111"), title_font=dict(color="#111111"))


def apply_plotly_layout(fig: go.Figure, **kwargs) -> go.Figure:
    xaxis = {**AXIS_STYLE, **kwargs.pop("xaxis", {})}
    yaxis = {**AXIS_STYLE, **kwargs.pop("yaxis", {})}
    fig.update_layout(**PLOTLY_LAYOUT, xaxis=xaxis, yaxis=yaxis, **kwargs)
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
        .hero-banner h1 {{
            color: white !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            margin: 0 0 0.5rem 0 !important;
            letter-spacing: -0.02em;
        }}
        .hero-banner p {{
            color: rgba(255,255,255,0.92);
            font-size: 1.05rem;
            line-height: 1.6;
            margin: 0;
        }}
        .metric-card {{
            background: {COLORS["card"]};
            border: 1px solid #E0E8E3;
            border-left: 4px solid {COLORS["gold"]};
            border-radius: 12px;
            padding: 1.1rem 1.25rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            height: 100%;
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
            font-size: 1.75rem;
            font-weight: 800;
            margin-top: 0.25rem;
        }}
        .section-title {{
            color: #111111;
            font-size: 1.35rem;
            font-weight: 700;
            border-bottom: 3px solid {COLORS["gold"]};
            padding-bottom: 0.35rem;
            margin: 1.5rem 0 1rem 0;
        }}
        .method-box {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #E0E8E3;
            line-height: 1.7;
            color: #111111;
        }}
        .method-box li, .method-box strong {{
            color: #111111;
        }}
        .footer-note {{
            text-align: center;
            color: #333333;
            font-size: 0.9rem;
            padding: 1.5rem;
            border-top: 1px solid #E0E8E3;
            margin-top: 2rem;
        }}
        div[data-testid="stMetric"] {{
            background: white;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            border: 1px solid #E0E8E3;
        }}
        div[data-testid="stMetricLabel"] {{
            color: #333333 !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: #111111 !important;
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
        label, .stSelectbox label, p, span, li {{
            color: #111111;
        }}
        [data-testid="stDataFrame"] {{
            color: #111111;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_csv(key: str) -> pd.DataFrame | None:
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
        f"**{label}** not found at `{path.relative_to(ROOT)}`. "
        "Re-run the upstream pipeline to generate it."
    )


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"


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


def horizontal_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str) -> go.Figure:
    plot_df = df.sort_values(x, ascending=True)
    fig = px.bar(
        plot_df,
        x=x,
        y=y,
        orientation="h",
        title=title,
        text=plot_df[x].apply(lambda v: pct(v)),
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


def render_hero(team_count: int | None) -> None:
    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>⚽ FIFA World Cup 2026 Forecast Engine V1</h1>
            <p>A probabilistic football forecasting system combining Elo ratings, squad value,
            betting market odds, Poisson goal modeling, Dixon-Coles correction,
            and {SIMULATIONS:,} Monte Carlo tournament simulations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    metrics = [
        ("Simulations", f"{SIMULATIONS:,}"),
        ("Historical Matches", HISTORICAL_MATCHES),
        ("Teams Modeled", str(team_count) if team_count else "—"),
        ("Model Version", MODEL_VERSION),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="label">{label}</div>'
                f'<div class="value">{value}</div></div>',
                unsafe_allow_html=True,
            )


def render_champion(df: pd.DataFrame | None) -> None:
    st.markdown('<div class="section-title">🏆 Champion Probability</div>', unsafe_allow_html=True)
    if df is None:
        warn_missing("champion", "Champion probabilities")
        return

    top = df.nlargest(20, "champion_prob").copy()
    col_chart, col_table = st.columns([3, 2])
    with col_chart:
        st.plotly_chart(
            horizontal_bar(top, "champion_prob", "team", "Top 20 — Title Probability", COLORS["gold"]),
            use_container_width=True,
        )
    with col_table:
        display = top[["team", "champion_prob", "titles"]].copy()
        display["champion_prob"] = display["champion_prob"].map(lambda x: pct(x, 2))
        display.columns = ["Team", "Champion Prob", "Sim Titles"]
        st.dataframe(display, hide_index=True, use_container_width=True, height=520)


def render_groups(df: pd.DataFrame | None) -> None:
    st.markdown(
        '<div class="section-title">📊 Group Qualification Probability</div>',
        unsafe_allow_html=True,
    )
    if df is None:
        warn_missing("groups", "Group stage simulation summary")
        return

    top = df.nlargest(30, "advance_prob").copy()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(name="Group Winner", x=top["team"], y=top["group_winner_prob"], marker_color=COLORS["pitch"])
    )
    fig.add_trace(
        go.Bar(name="Top 2", x=top["team"], y=top["group_top2_prob"], marker_color=COLORS["pitch_light"])
    )
    fig.add_trace(
        go.Bar(name="Advance (incl. 3rd)", x=top["team"], y=top["advance_prob"], marker_color=COLORS["gold"])
    )
    apply_plotly_layout(
        fig,
        barmode="group",
        title="Top 30 Teams by Advance Probability",
        height=480,
        xaxis=dict(tickangle=-45, title=""),
        yaxis=dict(tickformat=".0%", title="Probability"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#111111")),
    )
    st.plotly_chart(fig, use_container_width=True)

    table = top[["team", "group_winner_prob", "group_top2_prob", "advance_prob"]].copy()
    for col in ["group_winner_prob", "group_top2_prob", "advance_prob"]:
        table[col] = table[col].map(lambda x: pct(x, 1))
    table.columns = ["Team", "Group Winner", "Top 2", "Advance"]
    st.dataframe(table, hide_index=True, use_container_width=True)


def render_intelligence(df: pd.DataFrame | None) -> None:
    st.markdown('<div class="section-title">🧠 Team Intelligence Ranking</div>', unsafe_allow_html=True)
    if df is None:
        warn_missing("intelligence", "Team intelligence")
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
        title="Attack vs Defense (bubble size = Intelligence Score)",
        labels={"attack_rating": "Attack Rating", "defense_rating": "Defense Rating"},
    )
    apply_plotly_layout(fig, height=420, coloraxis_colorbar=dict(title="Intel Score"))
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
    table.columns = ["Team", "Elo", "Squad Value", "Market Title Prob", "Intel Score V2", "Attack", "Defense"]
    st.dataframe(table, hide_index=True, use_container_width=True)


def wc_team_set(groups_df: pd.DataFrame | None, champion_df: pd.DataFrame | None) -> set[str] | None:
    if groups_df is not None and "team" in groups_df.columns:
        return set(groups_df["team"])
    if champion_df is not None and "team" in champion_df.columns:
        return set(champion_df["team"])
    return None


def render_matchup_explorer(
    matchups: pd.DataFrame | None,
    intel: pd.DataFrame | None,
    wc_teams: set[str] | None = None,
) -> None:
    st.markdown('<div class="section-title">⚔️ Matchup Explorer</div>', unsafe_allow_html=True)
    if matchups is None:
        warn_missing("matchups", "Match strength matrix")
        return

    matrix_teams = set(matchups["home_team"]) | set(matchups["away_team"])
    if wc_teams:
        teams = sorted(wc_teams)
        in_matrix = len(wc_teams & matrix_teams)
        st.caption(
            f"World Cup 2026 squad list ({len(teams)} teams). "
            f"Pre-computed matchups available for {in_matrix} teams."
        )
    else:
        teams = sorted(matrix_teams)
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
        st.info(f"No pre-computed row for **{team_a}** vs **{team_b}** (home/away). Try swapping teams.")
        return

    r = row.iloc[0]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{team_a} xG", f"{r['expected_home_goals']:.2f}")
    m2.metric(f"{team_b} xG", f"{r['expected_away_goals']:.2f}")
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
            text=outcomes["Probability"].map(lambda x: pct(x, 1)),
            color="Outcome",
            color_discrete_map={
                f"{team_a} Win": COLORS["pitch"],
                "Draw": COLORS["draw"],
                f"{team_b} Win": COLORS["away"],
            },
            title="Match Outcome Probabilities",
        )
        apply_plotly_layout(fig, height=340, showlegend=False)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        scorelines = parse_scorelines(r["top_5_scorelines"])
        if scorelines:
            sl_df = pd.DataFrame(scorelines, columns=["Scoreline", "Probability"])
            fig2 = horizontal_bar(sl_df, "Probability", "Scoreline", "Top 5 Scorelines", COLORS["gold"])
            fig2.update_layout(height=340)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("Top scorelines unavailable for this matchup.")


def render_bracket_preview(brackets: pd.DataFrame | None) -> None:
    if brackets is None:
        return
    with st.expander("🗓️ Sample Knockout Bracket Preview (Simulation #1 — Round of 32)"):
        sample = brackets[(brackets["simulation_id"] == 1) & (brackets["round"] == "Round of 32")].copy()
        if sample.empty:
            st.caption("No Round of 32 data in bracket file.")
            return
        preview = sample[["match_id", "home_team", "away_team", "venue", "date_utc"]].head(16)
        preview.columns = ["Match", "Home", "Away", "Venue", "Kickoff (UTC)"]
        st.dataframe(preview, hide_index=True, use_container_width=True)


def render_methodology() -> None:
    st.markdown('<div class="section-title">📐 Methodology</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="method-box">
        <ul>
            <li><strong>Historical match database</strong> — 49,000+ international matches for training and calibration.</li>
            <li><strong>Elo rating system</strong> — Dynamic team strength updated match-by-match.</li>
            <li><strong>Attack / Defense strength ratings</strong> — Poisson-style offensive and defensive parameters per team.</li>
            <li><strong>Transfermarkt squad value layer</strong> — Market-value signal for squad quality depth.</li>
            <li><strong>Betting odds market calibration</strong> — Title odds from bookmakers anchor championship priors.</li>
            <li><strong>Market-calibrated match xG</strong> — Shrinkage on attack/defense ratings plus market strength in single-match expected goals.</li>
            <li><strong>Poisson goal model</strong> — Expected goals and scoreline distributions for each fixture.</li>
            <li><strong>Dixon-Coles low-score correction</strong> — Adjusts 0–0, 1–0, 0–1, 1–1 probabilities.</li>
            <li><strong>Monte Carlo tournament simulation</strong> — 20,000 full tournament draws from group stage through the final.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="FIFA World Cup 2026 Forecast Engine V1",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()

    champion_df = load_csv("champion")
    groups_df = load_csv("groups")
    intel_df = load_csv("intelligence")
    matchups_df = load_csv("matchups")
    brackets_df = load_csv("brackets")

    team_count = intel_df["team"].nunique() if intel_df is not None else None

    render_hero(team_count)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏆 Champion", "📊 Groups", "🧠 Intelligence", "⚔️ Matchups", "📐 Methodology"]
    )

    with tab1:
        render_champion(champion_df)
        render_bracket_preview(brackets_df)

    with tab2:
        render_groups(groups_df)

    with tab3:
        render_intelligence(intel_df)

    with tab4:
        render_matchup_explorer(matchups_df, intel_df, wc_team_set(groups_df, champion_df))

    with tab5:
        render_methodology()

    st.markdown(
        """
        <div class="footer-note">
        This is a V1 base forecast. Final squad, injury, suspension, odds updates,
        and tactical news layers will be added after final squad announcements.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
