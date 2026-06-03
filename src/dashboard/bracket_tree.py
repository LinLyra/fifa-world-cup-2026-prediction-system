"""
Most-likely knockout bracket + HTML bracket (flag vs flag layout).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
import pandas as pd

KNOCKOUT_LINKS: list[tuple[int, int, int]] = [
    (89, 73, 77),
    (90, 74, 78),
    (91, 76, 80),
    (92, 79, 83),
    (93, 81, 84),
    (94, 82, 85),
    (95, 86, 87),
    (96, 88, 75),
    (97, 89, 90),
    (98, 93, 94),
    (99, 91, 92),
    (100, 95, 96),
    (101, 97, 98),
    (102, 99, 100),
    (104, 101, 102),
]

LEFT_R32 = [73, 74, 76, 79, 81, 82, 86, 88]
RIGHT_R32 = [75, 77, 78, 80, 83, 84, 85, 87]

R32_SLOT_LABELS: dict[int, tuple[str, str]] = {
    73: ("Runner-up Group A", "Runner-up Group B"),
    74: ("Winner Group C", "Runner-up Group F"),
    75: ("Winner Group E", "Best 3rd (Groups A/B/C/D/F)"),
    76: ("Winner Group F", "Runner-up Group C"),
    77: ("Runner-up Group E", "Runner-up Group I"),
    78: ("Winner Group I", "Best 3rd (Groups C/D/F/G/H)"),
    79: ("Winner Group A", "Best 3rd (Groups C/E/F/H/I)"),
    80: ("Winner Group L", "Best 3rd (Groups E/H/I/J/K)"),
    81: ("Winner Group G", "Best 3rd (Groups A/E/H/I/J)"),
    82: ("Winner Group D", "Best 3rd (Groups B/E/F/I/J)"),
    83: ("Runner-up Group K", "Runner-up Group L"),
    84: ("Winner Group H", "Runner-up Group J"),
    85: ("Winner Group B", "Best 3rd (Groups E/F/G/I/J)"),
    86: ("Runner-up Group D", "Runner-up Group G"),
    87: ("Winner Group J", "Runner-up Group H"),
    88: ("Winner Group K", "Best 3rd (Groups D/E/I/J/L)"),
}
LEFT_R16 = [89, 90, 91, 92]
RIGHT_R16 = [93, 94, 95, 96]
LEFT_QF = [97, 98]
RIGHT_QF = [99, 100]
LEFT_SF = [101]
RIGHT_SF = [102]

# ISO-style flag emojis for World Cup 2026 teams
TEAM_FLAG: dict[str, str] = {
    "Algeria": "🇩🇿",
    "Argentina": "🇦🇷",
    "Australia": "🇦🇺",
    "Austria": "🇦🇹",
    "Belgium": "🇧🇪",
    "Bosnia and Herzegovina": "🇧🇦",
    "Brazil": "🇧🇷",
    "Canada": "🇨🇦",
    "Cape Verde": "🇨🇻",
    "Colombia": "🇨🇴",
    "Croatia": "🇭🇷",
    "Curaçao": "🇨🇼",
    "Czechia": "🇨🇿",
    "Democratic Republic of Congo": "🇨🇩",
    "Ecuador": "🇪🇨",
    "Egypt": "🇪🇬",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Ghana": "🇬🇭",
    "Haiti": "🇭🇹",
    "Iran": "🇮🇷",
    "Iraq": "🇮🇶",
    "Ivory Coast": "🇨🇮",
    "Japan": "🇯🇵",
    "Jordan": "🇯🇴",
    "Mexico": "🇲🇽",
    "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱",
    "New Zealand": "🇳🇿",
    "Norway": "🇳🇴",
    "Panama": "🇵🇦",
    "Paraguay": "🇵🇾",
    "Portugal": "🇵🇹",
    "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Senegal": "🇸🇳",
    "South Africa": "🇿🇦",
    "South Korea": "🇰🇷",
    "Spain": "🇪🇸",
    "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭",
    "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷",
    "United States": "🇺🇸",
    "Uruguay": "🇺🇾",
    "Uzbekistan": "🇺🇿",
}


def flag(team: str) -> str:
    return TEAM_FLAG.get(team, "🏳️")


@dataclass
class BracketMatch:
    match_id: int
    round: str
    side: str
    home: str
    away: str
    winner: str
    p_home: float
    p_away: float
    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_match_lookup(matrix: pd.DataFrame) -> dict[tuple[str, str], tuple[float, float, float]]:
    lookup: dict[tuple[str, str], tuple[float, float, float]] = {}
    for _, row in matrix.iterrows():
        lookup[(row["home_team"], row["away_team"])] = (
            float(row["home_win_prob"]),
            float(row["draw_prob"]),
            float(row["away_win_prob"]),
        )
    return lookup


def knockout_win_probs(
    team_a: str, team_b: str, lookup: dict[tuple[str, str], tuple[float, float, float]]
) -> tuple[float, float]:
    if (team_a, team_b) in lookup:
        hw, dr, aw = lookup[(team_a, team_b)]
    elif (team_b, team_a) in lookup:
        aw, dr, hw = lookup[(team_b, team_a)]
    else:
        return 0.5, 0.5
    p_a = hw + dr * 0.5
    p_b = aw + dr * 0.5
    total = p_a + p_b
    if total <= 0:
        return 0.5, 0.5
    return p_a / total, p_b / total


def pick_winner(
    team_a: str, team_b: str, lookup: dict[tuple[str, str], tuple[float, float, float]]
) -> tuple[str, float, float]:
    p_a, p_b = knockout_win_probs(team_a, team_b, lookup)
    if p_a >= p_b:
        return team_a, p_a, p_b
    return team_b, p_a, p_b


def _r32_bracket_signature(sim_r32: pd.DataFrame) -> str:
    """Canonical key for a full 16-match Round of 32 draw."""
    parts = []
    for _, row in sim_r32.sort_values("match_id").iterrows():
        parts.append(f"{int(row['match_id'])}:{row['home_team']}|{row['away_team']}")
    return ";".join(parts)


def _r32_draw_is_valid(sim_r32: pd.DataFrame) -> bool:
    teams = []
    for col in ("home_team", "away_team"):
        for val in sim_r32[col]:
            if pd.notna(val) and str(val).strip():
                teams.append(str(val))
    return len(teams) == 32 and len(set(teams)) == 32


def load_modal_r32(brackets: pd.DataFrame) -> dict[int, tuple[str, str, str]]:
    """Most frequent *complete* Round of 32 draw (joint modal), not per-match modes."""
    r32 = brackets[brackets["round"] == "Round of 32"].copy()
    if r32.empty:
        return {}

    sig_counts: dict[str, int] = {}
    sig_draws: dict[str, dict[int, tuple[str, str, str]]] = {}

    for sim_id, sim_df in r32.groupby("simulation_id"):
        if not _r32_draw_is_valid(sim_df):
            continue
        sig = _r32_bracket_signature(sim_df)
        sig_counts[sig] = sig_counts.get(sig, 0) + 1
        if sig not in sig_draws:
            draw: dict[int, tuple[str, str, str]] = {}
            for _, row in sim_df.sort_values("match_id").iterrows():
                mid = int(row["match_id"])
                draw[mid] = (
                    "Round of 32",
                    str(row["home_team"]),
                    str(row["away_team"]),
                )
            sig_draws[sig] = draw

    if not sig_counts:
        return {}

    best_sig = max(sig_counts, key=sig_counts.get)
    return sig_draws[best_sig]


def load_r32_template(brackets: pd.DataFrame, sim_id: int = 1) -> dict[int, tuple[str, str, str]]:
    sub = brackets[brackets["simulation_id"] == sim_id].copy()
    if sub.empty:
        sub = brackets[brackets["simulation_id"] == brackets["simulation_id"].min()].copy()
    out: dict[int, tuple[str, str, str]] = {}
    for _, row in sub.iterrows():
        if str(row.get("round", "")) != "Round of 32":
            continue
        out[int(row["match_id"])] = (
            "Round of 32",
            str(row["home_team"]),
            str(row["away_team"]),
        )
    return out


def _simulate_ko_winner(
    team_a: str,
    team_b: str,
    lookup: dict[tuple[str, str], tuple[float, float, float]],
    rng: np.random.Generator,
) -> str:
    p_a, p_b = knockout_win_probs(team_a, team_b, lookup)
    return str(rng.choice([team_a, team_b], p=[p_a, p_b]))


def compute_reach_probs(
    brackets: pd.DataFrame,
    match_matrix: pd.DataFrame,
) -> pd.DataFrame:
    """Knockout round reach rates from Monte Carlo bracket file + KO simulation."""
    lookup = build_match_lookup(match_matrix)
    r32_all = brackets[brackets["round"] == "Round of 32"]
    n_sims = int(r32_all["simulation_id"].nunique())
    if n_sims == 0:
        return pd.DataFrame()

    counts: dict[str, dict[str, int]] = {}

    def bump(team: str, stage: str) -> None:
        counts.setdefault(team, {})
        counts[team][stage] = counts[team].get(stage, 0) + 1

    for sim_id, sim_df in r32_all.groupby("simulation_id"):
        rng = np.random.default_rng(int(sim_id) % (2**31))
        r32: dict[int, tuple[str, str]] = {
            int(r["match_id"]): (str(r["home_team"]), str(r["away_team"]))
            for _, r in sim_df.iterrows()
        }
        winners: dict[int, str] = {}

        for mid, (home, away) in r32.items():
            bump(home, "r32")
            bump(away, "r32")
            w = _simulate_ko_winner(home, away, lookup, rng)
            winners[mid] = w
            bump(w, "r16")

        for mid, feed_a, feed_b in KNOCKOUT_LINKS:
            home = winners[feed_a]
            away = winners[feed_b]
            w = _simulate_ko_winner(home, away, lookup, rng)
            winners[mid] = w
            if 89 <= mid <= 96:
                bump(w, "qf")
            elif 97 <= mid <= 100:
                bump(w, "sf")
            elif mid in (101, 102):
                bump(w, "final")
            elif mid == 104:
                bump(w, "win")

    rows = []
    for team, stages in counts.items():
        rows.append(
            {
                "team": team,
                "reach_r32": stages.get("r32", 0) / n_sims,
                "reach_r16": stages.get("r16", 0) / n_sims,
                "reach_qf": stages.get("qf", 0) / n_sims,
                "reach_sf": stages.get("sf", 0) / n_sims,
                "reach_final": stages.get("final", 0) / n_sims,
                "reach_win": stages.get("win", 0) / n_sims,
            }
        )
    return pd.DataFrame(rows)


MATCH_DISPLAY_ORDER: list[int] = (
    LEFT_R32 + RIGHT_R32 + LEFT_R16 + RIGHT_R16 + LEFT_QF + RIGHT_QF + LEFT_SF + RIGHT_SF + [104]
)


def path_chain_ordered(matches: list[BracketMatch], path_ids: set[int]) -> list[BracketMatch]:
    by_id = _by_id(matches)
    return [by_id[mid] for mid in MATCH_DISPLAY_ORDER if mid in path_ids and mid in by_id]


def build_most_likely_path(
    brackets: pd.DataFrame,
    match_matrix: pd.DataFrame,
    sim_id: int | None = None,
) -> list[BracketMatch]:
    lookup = build_match_lookup(match_matrix)
    r32 = load_modal_r32(brackets) if sim_id is None else load_r32_template(brackets, sim_id)
    participants: dict[int, str] = {}
    all_matches: list[BracketMatch] = []

    for mid, (rnd, home, away) in r32.items():
        winner, p_h, p_a = pick_winner(home, away, lookup)
        participants[mid] = winner
        side = "left" if mid in LEFT_R32 else "right"
        all_matches.append(
            BracketMatch(mid, rnd, side, home, away, winner, p_h, p_a)
        )

    def _round_name(match_id: int) -> str:
        if match_id == 104:
            return "Final"
        if match_id in (101, 102):
            return "Semi-final"
        if 97 <= match_id <= 100:
            return "Quarter-final"
        if 89 <= match_id <= 96:
            return "Round of 16"
        return "Round of 32"

    for mid, feed_a, feed_b in KNOCKOUT_LINKS:
        home = participants[feed_a]
        away = participants[feed_b]
        winner, p_h, p_a = pick_winner(home, away, lookup)
        participants[mid] = winner
        if mid in LEFT_R16 + LEFT_QF + LEFT_SF:
            side = "left"
        elif mid in RIGHT_R16 + RIGHT_QF + RIGHT_SF:
            side = "right"
        else:
            side = "center"
        all_matches.append(
            BracketMatch(
                mid, _round_name(mid), side, home, away, winner, p_h, p_a
            )
        )

    return all_matches


def _by_id(matches: list[BracketMatch]) -> dict[int, BracketMatch]:
    return {m.match_id: m for m in matches}


def _child_match(feeder_id: int) -> int | None:
    for to_id, feed_a, feed_b in KNOCKOUT_LINKS:
        if feed_a == feeder_id or feed_b == feeder_id:
            return to_id
    return None


def trace_team_path(matches: list[BracketMatch], team: str | None) -> set[int]:
    """Match IDs on this team's advancement chain in the most-likely bracket."""
    if not team:
        return set()
    by_id = _by_id(matches)
    start = next(
        (
            m
            for m in matches
            if m.match_id in LEFT_R32 + RIGHT_R32 and team in (m.home, m.away)
        ),
        None,
    )
    if not start:
        return set()

    path: set[int] = set()
    mid: int | None = start.match_id
    while mid is not None and mid in by_id:
        m = by_id[mid]
        path.add(mid)
        if m.winner != team:
            break
        mid = _child_match(mid)
    return path


def _match_card_html(
    m: BracketMatch,
    active_team: str | None,
    champ: dict[str, float],
    path_diff: dict[str, float],
    path_ids: set[int],
) -> str:
    on_path = m.match_id in path_ids
    dim = active_team and not on_path
    border = "#38bdf8" if on_path else "#334155"
    bg = "#1e3a5f" if on_path else "#0f172a"
    opacity = "0.32" if dim else "1"
    p_home_pct = f"{m.p_home * 100:.1f}%"
    p_away_pct = f"{m.p_away * 100:.1f}%"
    home_win = m.winner == m.home
    away_win = m.winner == m.away
    home_style = "winner" if home_win else ""
    away_style = "winner" if away_win else ""
    if active_team == m.home:
        home_style += " tracked"
    if active_team == m.away:
        away_style += " tracked"
    tooltip = (
        f"{m.round}: {m.home} {p_home_pct} — {m.away} {p_away_pct} "
        f"(KO advance, sums to 100%) → {m.winner}"
    )
    return f"""
    <div class="match-card" style="border-color:{border};background:{bg};opacity:{opacity}"
         title="{tooltip}">
      <div class="team {home_style}">
        <span class="flag">{flag(m.home)}</span>
        <span class="name">{m.home}</span>
        <span class="pct">{p_home_pct}</span>
      </div>
      <div class="vs">VS</div>
      <div class="team {away_style}">
        <span class="flag">{flag(m.away)}</span>
        <span class="name">{m.away}</span>
        <span class="pct">{p_away_pct}</span>
      </div>
    </div>
    """


def _round_column(
    title: str,
    match_ids: list[int],
    by_id: dict[int, BracketMatch],
    active_team: str | None,
    champ: dict[str, float],
    path_diff: dict[str, float],
    path_ids: set[int],
    focus_only: bool = False,
) -> str:
    cards = []
    for mid in match_ids:
        if mid not in by_id:
            continue
        if focus_only and active_team and mid not in path_ids:
            continue
        cards.append(
            '<div class="slot">'
            + _match_card_html(by_id[mid], active_team, champ, path_diff, path_ids)
            + "</div>"
        )
    if focus_only and active_team and not cards:
        return ""
    return f"""
    <div class="round-col">
      <div class="round-label">{title}</div>
      <div class="round-slots">{''.join(cards)}</div>
    </div>
    """


def render_bracket_svg(
    matches: list[BracketMatch],
    active_team: str | None,
    champion_probs: dict[str, float],
    path_difficulty: dict[str, float],
    path_ids: set[int] | None = None,
    focus_only: bool = False,
) -> str:
    """Classic left / center / right bracket with flag vs flag match cards."""
    by_id = _by_id(matches)
    champ = champion_probs or {}
    path_diff = path_difficulty or {}
    path_ids = path_ids if path_ids is not None else trace_team_path(matches, active_team)
    focus = focus_only and bool(active_team)

    col_kw = dict(
        by_id=by_id,
        active_team=active_team,
        champ=champ,
        path_diff=path_diff,
        path_ids=path_ids,
        focus_only=focus,
    )

    left = (
        _round_column("R32", LEFT_R32, **col_kw)
        + _round_column("R16", LEFT_R16, **col_kw)
        + _round_column("QF", LEFT_QF, **col_kw)
        + _round_column("SF", LEFT_SF, **col_kw)
    )

    right = (
        _round_column("SF", RIGHT_SF, **col_kw)
        + _round_column("QF", RIGHT_QF, **col_kw)
        + _round_column("R16", RIGHT_R16, **col_kw)
        + _round_column("R32", RIGHT_R32, **col_kw)
    )

    final_html = ""
    show_final = 104 in by_id and (not focus or 104 in path_ids)
    if show_final:
        f = by_id[104]
        final_html = f"""
        <div class="final-col">
          <div class="trophy">🏆 World Cup Final</div>
          {_match_card_html(f, active_team, champ, path_diff, path_ids)}
          <div class="final-meta">
            Most likely final<br>
            {flag(f.home)} <strong>{f.home}</strong> vs {flag(f.away)} <strong>{f.away}</strong>
          </div>
        </div>
        """

    css = """
    <style>
    html, body {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #0c1222;
      font-family: Inter, system-ui, sans-serif;
    }
    .brv-root {
      display: flex;
      flex-direction: column;
      height: 100%;
      max-height: 640px;
      box-sizing: border-box;
    }
    .brv-toolbar {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      background: #1e293b;
      border-bottom: 1px solid #334155;
      color: #e2e8f0;
      font-size: 13px;
      user-select: none;
    }
    .brv-toolbar button {
      background: #334155;
      color: #f1f5f9;
      border: 1px solid #475569;
      border-radius: 6px;
      min-width: 36px;
      height: 32px;
      cursor: pointer;
      font-size: 16px;
      font-weight: 700;
      line-height: 1;
    }
    .brv-toolbar button:hover { background: #475569; }
    .brv-pct-input {
      width: 52px;
      height: 32px;
      padding: 4px 6px;
      border-radius: 6px;
      border: 1px solid #475569;
      background: #0f172a;
      color: #f1f5f9;
      font-size: 13px;
      font-weight: 700;
      text-align: center;
    }
    .brv-pct-suffix { color: #94a3b8; font-size: 12px; margin-left: 2px; }
    .brv-hint { color: #94a3b8; font-size: 11px; margin-left: auto; }
    .brv-canvas {
      flex: 1;
      overflow: auto;
      cursor: grab;
      min-height: 0;
      background: linear-gradient(180deg, #0c1222 0%, #0f172a 100%);
      -webkit-overflow-scrolling: touch;
    }
    .brv-canvas.dragging { cursor: grabbing; }
    .brv-spacer { position: relative; display: inline-block; min-width: 100%; }
    .brv-stage {
      transform-origin: top left;
      display: inline-block;
      padding: 12px 32px 28px 16px;
    }
    .bracket-wrap { background: transparent; border-radius: 0; padding: 0; }
    .bracket-grid {
      display: flex;
      align-items: stretch;
      justify-content: center;
      gap: 10px;
      width: max-content;
      min-height: 680px;
    }
    .bracket-side { display: flex; gap: 8px; align-items: stretch; }
    /* Right: SF→QF→R16→R32 outward to the right edge (mirror of left side). */
    .bracket-side.right { flex-direction: row; }
    .round-col {
      width: 172px;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
    }
    .round-slots {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-around;
      gap: 4px;
    }
    .slot { flex-shrink: 0; }
    .round-label {
      text-align: center;
      color: #94a3b8;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
      text-transform: uppercase;
    }
    .match-card {
      border: 2px solid #334155;
      border-radius: 8px;
      padding: 6px 8px;
      margin-bottom: 4px;
    }
    .team {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 3px 2px;
      border-radius: 6px;
    }
    .team.winner {
      background: rgba(59, 130, 246, 0.2);
      border: 1px solid #3b82f6;
    }
    .team.tracked {
      background: rgba(251, 191, 36, 0.35);
      border: 2px solid #fbbf24;
      box-shadow: 0 0 8px rgba(251, 191, 36, 0.5);
    }
    .flag { font-size: 18px; line-height: 1; flex-shrink: 0; }
    .name {
      flex: 1;
      color: #e2e8f0;
      font-size: 10px;
      font-weight: 600;
      line-height: 1.2;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .pct { color: #94a3b8; font-size: 10px; min-width: 36px; text-align: right; flex-shrink: 0; }
    .vs {
      text-align: center;
      color: #64748b;
      font-size: 9px;
      font-weight: 800;
      margin: 1px 0;
    }
    .final-col {
      width: 180px;
      flex-shrink: 0;
      padding: 0 6px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      align-self: center;
    }
    .trophy {
      color: #fbbf24;
      font-size: 16px;
      font-weight: 800;
      margin-bottom: 10px;
    }
    .final-meta {
      margin-top: 10px;
      color: #cbd5e1;
      font-size: 11px;
      text-align: center;
      line-height: 1.5;
    }
    .journey-lane {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      flex-wrap: nowrap;
      padding: 8px 0 16px;
      overflow-x: auto;
    }
    .journey-step { flex-shrink: 0; width: 168px; }
    .journey-arrow {
      color: #64748b;
      font-size: 18px;
      font-weight: 800;
      flex-shrink: 0;
    }
    .bracket-grid.focused {
      min-height: 220px;
      justify-content: center;
    }
    .connector-hint {
      color: #94a3b8;
      font-size: 11px;
      text-align: center;
      margin: 0 0 10px 0;
      padding: 0 12px;
    }
    </style>
    """

    hint = ""
    if active_team:
        chain = path_chain_ordered(matches, path_ids)
        stops = " → ".join(
            f"{m.round.replace('Round of ', 'R')}" for m in chain
        )
        hint = (
            f'<p class="connector-hint">Most probable knockout route for '
            f'{flag(active_team)} <strong style="color:#fbbf24">{active_team}</strong>'
            f' — not a guaranteed path. Stops when the model favours an opponent.<br>'
            f'<span style="color:#38bdf8">{stops or "R32 only"}</span></p>'
        )

    journey_html = ""
    if focus and path_ids:
        steps = []
        chain = path_chain_ordered(matches, path_ids)
        for i, m in enumerate(chain):
            if i:
                steps.append('<div class="journey-arrow">→</div>')
            steps.append(
                '<div class="journey-step">'
                + _match_card_html(m, active_team, champ, path_diff, path_ids)
                + "</div>"
            )
        journey_html = '<div class="journey-lane">' + "".join(steps) + "</div>"

    if focus and path_ids:
        inner = hint + journey_html
    else:
        inner = (
            hint
            + '<div class="bracket-grid">'
            + '<div class="bracket-side left">'
            + left
            + "</div>"
            + final_html
            + '<div class="bracket-side right">'
            + right
            + "</div>"
            + "</div>"
        )

    js = """
    <script>
    (function () {
      var canvas = document.getElementById("brv-canvas");
      var stage = document.getElementById("brv-stage");
      var spacer = document.getElementById("brv-spacer");
      var pctInput = document.getElementById("brv-pct-in");
      var scale = 0.8;
      var drag = false, sx, sy, sl, st;
      var MIN_SCALE = 0.35;
      var MAX_SCALE = 1.35;

      function applyScale() {
        stage.style.transform = "scale(" + scale + ")";
        spacer.style.width = Math.ceil(stage.offsetWidth * scale) + "px";
        spacer.style.height = Math.ceil(stage.offsetHeight * scale) + "px";
        if (pctInput && document.activeElement !== pctInput) {
          pctInput.value = Math.round(scale * 100);
        }
      }

      function setScalePercent(pct) {
        var target = Math.max(MIN_SCALE, Math.min(MAX_SCALE, pct / 100));
        var c = viewportCenter();
        zoomAt(c[0], c[1], target - scale);
      }

      function zoomAt(clientX, clientY, delta) {
        var rect = canvas.getBoundingClientRect();
        var mx = clientX - rect.left + canvas.scrollLeft;
        var my = clientY - rect.top + canvas.scrollTop;
        var oldScale = scale;
        scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale + delta));
        if (scale === oldScale) return;
        applyScale();
        var ratio = scale / oldScale;
        canvas.scrollLeft = Math.max(0, mx * ratio - (clientX - rect.left));
        canvas.scrollTop = Math.max(0, my * ratio - (clientY - rect.top));
      }

      function viewportCenter() {
        var rect = canvas.getBoundingClientRect();
        return [rect.left + rect.width / 2, rect.top + rect.height / 2];
      }

      function fitView() {
        var cw = canvas.clientWidth - 24;
        var ch = canvas.clientHeight - 24;
        stage.style.transform = "scale(1)";
        spacer.style.width = stage.offsetWidth + "px";
        spacer.style.height = stage.offsetHeight + "px";
        var sw = stage.offsetWidth;
        var sh = stage.offsetHeight;
        scale = Math.min(cw / sw, ch / sh, 0.95);
        scale = Math.max(MIN_SCALE, scale);
        applyScale();
        canvas.scrollLeft = Math.max(0, (spacer.offsetWidth - cw) / 2);
        canvas.scrollTop = Math.max(0, (spacer.offsetHeight - ch) / 2);
      }

      document.getElementById("brv-in").onclick = function () {
        var c = viewportCenter();
        zoomAt(c[0], c[1], 0.08);
      };
      document.getElementById("brv-out").onclick = function () {
        var c = viewportCenter();
        zoomAt(c[0], c[1], -0.08);
      };
      document.getElementById("brv-fit").onclick = fitView;

      pctInput.addEventListener("change", function () {
        setScalePercent(parseFloat(pctInput.value) || 80);
      });
      pctInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          setScalePercent(parseFloat(pctInput.value) || 80);
          pctInput.blur();
        }
      });

      canvas.addEventListener("mousedown", function (e) {
        if (e.button !== 0) return;
        drag = true;
        sx = e.clientX;
        sy = e.clientY;
        sl = canvas.scrollLeft;
        st = canvas.scrollTop;
        canvas.classList.add("dragging");
        e.preventDefault();
      });
      window.addEventListener("mousemove", function (e) {
        if (!drag) return;
        canvas.scrollLeft = sl - (e.clientX - sx);
        canvas.scrollTop = st - (e.clientY - sy);
      });
      window.addEventListener("mouseup", function () {
        drag = false;
        canvas.classList.remove("dragging");
      });
      canvas.addEventListener("wheel", function (e) {
        e.preventDefault();
        var delta = e.deltaY < 0 ? 0.05 : -0.05;
        zoomAt(e.clientX, e.clientY, delta);
      }, { passive: false });

      applyScale();
      setTimeout(function () {
        var cw = canvas.clientWidth;
        var ch = canvas.clientHeight;
        canvas.scrollLeft = Math.max(0, (spacer.offsetWidth - cw) / 2);
        canvas.scrollTop = Math.max(0, (spacer.offsetHeight - ch) / 2);
      }, 120);
    })();
    </script>
    """

    return (
        css
        + '<div class="brv-root">'
        + '<div class="brv-toolbar">'
        + '<button type="button" id="brv-out" title="Zoom out">−</button>'
        + '<input type="number" class="brv-pct-input" id="brv-pct-in" '
        + 'min="35" max="135" step="1" value="80" title="Zoom % (editable)" />'
        + '<span class="brv-pct-suffix">%</span>'
        + '<button type="button" id="brv-in" title="Zoom in">+</button>'
        + '<button type="button" id="brv-fit" title="Fit to view">Fit</button>'
        + '<span class="brv-hint">Drag · scroll · type zoom % · Fit</span>'
        + "</div>"
        + '<div class="brv-canvas" id="brv-canvas">'
        + '<div class="brv-spacer" id="brv-spacer">'
        + '<div class="brv-stage" id="brv-stage">'
        + '<div class="bracket-wrap">'
        + inner
        + "</div></div></div></div></div>"
        + js
    )


def export_bracket_json(
    matches: list[BracketMatch],
    out_path,
    champion_df: pd.DataFrame | None = None,
    path_df: pd.DataFrame | None = None,
) -> None:
    import json
    from pathlib import Path

    payload = {
        "matches": [m.to_dict() for m in matches],
        "links": [{"to": t, "from_a": a, "from_b": b} for t, a, b in KNOCKOUT_LINKS],
        "flags": TEAM_FLAG,
        "champion_probs": (
            champion_df.set_index("team")["champion_prob"].to_dict()
            if champion_df is not None
            else {}
        ),
        "path_difficulty": (
            path_df.set_index("team")["expected_path_difficulty"].to_dict()
            if path_df is not None and "expected_path_difficulty" in path_df.columns
            else {}
        ),
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
