#!/usr/bin/env python3
"""Export CSV outputs to JSON for the React / Vercel dashboard."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dashboard.bracket_tree import (  # noqa: E402
    build_most_likely_path,
    compute_reach_probs,
    export_bracket_json,
)

OUT_DIR = ROOT / "frontend/public/data"


def write_records(df: pd.DataFrame, path: Path) -> None:
    df.to_json(path, orient="records", indent=2)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    brackets = pd.read_csv(ROOT / "data/predictions/world_cup_brackets_v1.csv")
    matrix = pd.read_csv(ROOT / "data/predictions/match_strength_matrix_v2.csv")
    champs = pd.read_csv(ROOT / "data/predictions/world_cup_champion_probabilities_v2.csv")
    groups = pd.read_csv(ROOT / "data/predictions/group_stage_simulation_v3_summary.csv")
    intel = pd.read_csv(ROOT / "data/features/team_intelligence_v2.csv")

    path_p = ROOT / "data/predictions/path_difficulty_v1.csv"
    path_df = pd.read_csv(path_p) if path_p.exists() else None

    final_p = ROOT / "data/intelligence/final_match_intelligence_v1.csv"
    final_df = pd.read_csv(final_p) if final_p.exists() else None

    fixtures_p = ROOT / "data/raw/group_fixtures_final.csv"
    fixtures_df = pd.read_csv(fixtures_p) if fixtures_p.exists() else None

    matches = build_most_likely_path(brackets, matrix)
    export_bracket_json(matches, OUT_DIR / "bracket_consensus.json", champs, path_df)

    write_records(champs, OUT_DIR / "champions.json")
    write_records(groups, OUT_DIR / "groups.json")
    write_records(intel, OUT_DIR / "intelligence.json")
    if path_df is not None:
        write_records(path_df, OUT_DIR / "path_difficulty.json")
    if final_df is not None:
        write_records(final_df, OUT_DIR / "final_match_intel.json")
    if fixtures_df is not None:
        write_records(fixtures_df, OUT_DIR / "fixtures.json")

    matrix.to_json(OUT_DIR / "match_matrix.json", orient="records", indent=2)

    reach = compute_reach_probs(brackets, matrix)
    if not reach.empty:
        write_records(reach, OUT_DIR / "reach_probs.json")

    teams = set(champs["team"])
    if fixtures_df is not None:
        teams = set(fixtures_df["home_team"]).union(set(fixtures_df["away_team"]))
    meta = {
        "engine": "V2 Pre-Match Forecast",
        "simulations": 20_000,
        "historical_matches": "49,000+",
        "team_count": len(teams),
    }
    (OUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Exported dashboard JSON to {OUT_DIR}")


if __name__ == "__main__":
    main()
