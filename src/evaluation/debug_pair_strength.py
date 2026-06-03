"""
Debug head-to-head strength for two teams (xG decomposition + KO win %).

Run:
  python src/evaluation/debug_pair_strength.py --team-a Iran --team-b "United States"
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import poisson

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from simulation.build_match_strength_matrix_v2 import (  # noqa: E402
    ATTACK_SHRINK,
    BASE_GOALS,
    DEFENSE_SHRINK,
    MAX_GOALS,
    MAX_XG,
    MIN_XG,
    RHO,
    expected_goals,
    score_matrix,
    summarize,
)

INTEL_FILE = ROOT / "data/features/team_intelligence_v2.csv"
MATRIX_FILE = ROOT / "data/predictions/match_strength_matrix_v2.csv"

PROFILE_COLS = [
    "elo",
    "attack_rating",
    "defense_rating",
    "intelligence_score_v2",
    "market_value_eur",
    "market_champion_prob",
    "market_score",
    "decimal_odds",
]


def ko_win_probs(home_win: float, draw: float, away_win: float) -> tuple[float, float]:
    p_home = home_win + draw * 0.5
    p_away = away_win + draw * 0.5
    total = p_home + p_away
    if total <= 0:
        return 0.5, 0.5
    return p_home / total, p_away / total


def bracket_style_ko(home: str, away: str, lookup: dict[tuple[str, str], tuple[float, float, float]]) -> tuple[float, float]:
    """Same orientation logic as dashboard.bracket_tree.knockout_win_probs."""
    if (home, away) in lookup:
        hw, dr, aw = lookup[(home, away)]
    elif (away, home) in lookup:
        aw, dr, hw = lookup[(away, home)]
    else:
        return 0.5, 0.5
    return ko_win_probs(hw, dr, aw)


def xg_breakdown(team_a: str, team_b: str, teams: pd.DataFrame) -> dict[str, float]:
    a = teams.loc[team_a]
    b = teams.loc[team_b]

    a_attack = ATTACK_SHRINK * a["attack_rating"] + (1 - ATTACK_SHRINK) * 1.0
    b_attack = ATTACK_SHRINK * b["attack_rating"] + (1 - ATTACK_SHRINK) * 1.0
    a_defense = DEFENSE_SHRINK * a["defense_rating"] + (1 - DEFENSE_SHRINK) * 1.0
    b_defense = DEFENSE_SHRINK * b["defense_rating"] + (1 - DEFENSE_SHRINK) * 1.0

    elo_diff = a["elo"] - b["elo"]
    intel_diff = a["intelligence_score_v2"] - b["intelligence_score_v2"]
    elo_mult_a = math.exp(elo_diff / 2000)
    elo_mult_b = math.exp(-elo_diff / 2000)
    intel_mult_a = math.exp(intel_diff / 2.2)
    intel_mult_b = math.exp(-intel_diff / 2.2)

    lh_raw = BASE_GOALS * a_attack * b_defense * elo_mult_a * intel_mult_a
    la_raw = BASE_GOALS * b_attack * a_defense * elo_mult_b * intel_mult_b
    lh = float(np.clip(lh_raw, MIN_XG, MAX_XG))
    la = float(np.clip(la_raw, MIN_XG, MAX_XG))

    return {
        "a_attack_shrunk": a_attack,
        "b_attack_shrunk": b_attack,
        "a_defense_shrunk": a_defense,
        "b_defense_shrunk": b_defense,
        "elo_diff": elo_diff,
        "intel_diff": intel_diff,
        "elo_mult_a": elo_mult_a,
        "elo_mult_b": elo_mult_b,
        "intel_mult_a": intel_mult_a,
        "intel_mult_b": intel_mult_b,
        "lh_raw": lh_raw,
        "la_raw": la_raw,
        "lh": lh,
        "la": la,
        "lh_clipped": lh != lh_raw,
        "la_clipped": la != la_raw,
    }


def match_from_matrix(home: str, away: str) -> pd.Series | None:
    if not MATRIX_FILE.exists():
        return None
    m = pd.read_csv(MATRIX_FILE)
    row = m[(m["home_team"] == home) & (m["away_team"] == away)]
    if row.empty:
        return None
    return row.iloc[0]


def print_profile(label: str, row: pd.Series) -> None:
    print(f"\n--- {label} ---")
    for col in PROFILE_COLS:
        if col not in row.index:
            continue
        val = row[col]
        if pd.isna(val):
            print(f"  {col:26s}  —")
        elif col == "market_value_eur":
            print(f"  {col:26s}  {val:,.0f}")
        elif col in ("market_champion_prob", "market_score", "intelligence_score_v2"):
            print(f"  {col:26s}  {float(val):.6f}")
        else:
            print(f"  {col:26s}  {float(val):.4f}")


def compare_profiles(a_row: pd.Series, b_row: pd.Series, team_a: str, team_b: str) -> None:
    print("\n" + "=" * 72)
    print("Signal comparison (A − B); positive => favors team A")
    print("=" * 72)
    for col in ["elo", "attack_rating", "defense_rating", "intelligence_score_v2"]:
        if col not in a_row.index or col not in b_row.index:
            continue
        av, bv = float(a_row[col]), float(b_row[col])
        diff = av - bv
        note = ""
        if col == "defense_rating":
            note = "  (lower defense_rating = stronger defense in xG formula)"
        print(f"  {col:26s}  A={av:.4f}  B={bv:.4f}  Δ={diff:+.4f}{note}")
    for col in ["market_value_eur", "market_champion_prob"]:
        if col not in a_row.index or col not in b_row.index:
            continue
        av, bv = a_row[col], b_row[col]
        if pd.isna(av) or pd.isna(bv):
            print(f"  {col:26s}  (missing for one side)")
            continue
        print(f"  {col:26s}  A={float(av):,.0f}  B={float(bv):,.0f}  Δ={float(av)-float(bv):+,.0f}")


def print_orientation(
    home: str,
    away: str,
    teams: pd.DataFrame,
    lookup: dict[tuple[str, str], tuple[float, float, float]],
) -> None:
    print("\n" + "=" * 72)
    print(f"Orientation: {home} (H) vs {away} (A)")
    print("=" * 72)

    bd = xg_breakdown(home, away, teams)
    print(
        f"  Shrunk attack/def:  H atk={bd['a_attack_shrunk']:.3f}  A atk={bd['b_attack_shrunk']:.3f}  "
        f"H def={bd['a_defense_shrunk']:.3f}  A def={bd['b_defense_shrunk']:.3f}"
    )
    print(
        f"  Elo diff (H−A): {bd['elo_diff']:+.1f}  → mult H={bd['elo_mult_a']:.4f}  A={bd['elo_mult_b']:.4f}"
    )
    print(
        f"  Intel diff (H−A): {bd['intel_diff']:+.4f}  → mult H={bd['intel_mult_a']:.4f}  A={bd['intel_mult_b']:.4f}"
    )
    clip_note = []
    if bd["lh_clipped"]:
        clip_note.append("home xG clipped")
    if bd["la_clipped"]:
        clip_note.append("away xG clipped")
    print(
        f"  xG raw: H={bd['lh_raw']:.3f}  A={bd['la_raw']:.3f}  "
        f"→ clipped: H={bd['lh']:.3f}  A={bd['la']:.3f}"
        + (f"  [{', '.join(clip_note)}]" if clip_note else "")
    )

    lh, la = expected_goals(home, away, teams)
    matrix = score_matrix(lh, la)
    summary = summarize(matrix)
    p_ko_h, p_ko_a = ko_win_probs(summary["home_win_prob"], summary["draw_prob"], summary["away_win_prob"])
    p_br_h, p_br_a = bracket_style_ko(home, away, lookup)

    print(
        f"  90-min:  H win {summary['home_win_prob']:.1%}  draw {summary['draw_prob']:.1%}  "
        f"A win {summary['away_win_prob']:.1%}"
    )
    print(f"  KO win (draw→0.5):  {home} {p_ko_h:.1%}  |  {away} {p_ko_a:.1%}")
    print(f"  Bracket lookup KO:   {home} {p_br_h:.1%}  |  {away} {p_br_a:.1%}")
    print(f"  Top scoreline: {summary['pred_home_score']}-{summary['pred_away_score']} "
          f"({summary['score_probability']:.1%})")

    cached = match_from_matrix(home, away)
    if cached is not None:
        print(
            f"  Matrix file:  H xG={cached['expected_home_goals']:.3f}  A xG={cached['expected_away_goals']:.3f}  "
            f"KO H={ko_win_probs(cached['home_win_prob'], cached['draw_prob'], cached['away_win_prob'])[0]:.1%}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug pair strength (xG + KO win).")
    parser.add_argument("--team-a", required=True, help="First team (canonical name)")
    parser.add_argument("--team-b", required=True, help="Second team (canonical name)")
    args = parser.parse_args()

    team_a, team_b = args.team_a.strip(), args.team_b.strip()

    intel = pd.read_csv(INTEL_FILE)
    required = ["team", "elo", "attack_rating", "defense_rating", "intelligence_score_v2"]
    missing_cols = [c for c in required if c not in intel.columns]
    if missing_cols:
        raise SystemExit(f"Missing columns in {INTEL_FILE}: {missing_cols}")

    teams = intel.dropna(subset=required).set_index("team")
    for name in (team_a, team_b):
        if name not in teams.index:
            close = [t for t in teams.index if name.lower() in t.lower() or t.lower() in name.lower()]
            hint = f" Close matches: {close[:8]}" if close else ""
            raise SystemExit(f"Team not found: {name!r}.{hint}")

    a_row = intel[intel["team"] == team_a].iloc[0]
    b_row = intel[intel["team"] == team_b].iloc[0]

    print("=" * 72)
    print(f"Pair debug: {team_a}  vs  {team_b}")
    print(f"Source: {INTEL_FILE.name} + build_match_strength_matrix_v2 formula")
    print("=" * 72)

    print_profile(team_a, a_row)
    print_profile(team_b, b_row)
    compare_profiles(a_row, b_row, team_a, team_b)

    lookup: dict[tuple[str, str], tuple[float, float, float]] = {}
    if MATRIX_FILE.exists():
        m = pd.read_csv(MATRIX_FILE)
        for _, r in m.iterrows():
            lookup[(r["home_team"], r["away_team"])] = (
                float(r["home_win_prob"]),
                float(r["draw_prob"]),
                float(r["away_win_prob"]),
            )

    print_orientation(team_a, team_b, teams, lookup)
    print_orientation(team_b, team_a, teams, lookup)

    print("\n" + "=" * 72)
    print("Notes")
    print("=" * 72)
    print(
        "  • Bracket consensus uses ONE directed matrix row; if only A(H) vs B exists,\n"
        "    B(H) vs A reuses swapped 90-min probs (dashboard.bracket_tree.knockout_win_probs).\n"
        "  • intelligence_score_v2 already blends elo (30%), market value (25%), odds (25%),\n"
        "    attack (10%), defense (7%), form (3%); xG then applies elo + intel multipliers again.\n"
        "  • This script does NOT apply market anchor — inspect only."
    )


if __name__ == "__main__":
    main()
