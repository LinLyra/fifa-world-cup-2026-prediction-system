from pathlib import Path
import re
import pandas as pd

RANKINGS_FILE = Path("data/predictions/group_stage_rankings_v3.csv")
SLOTS_FILE = Path("data/raw/knockout_slots.csv")
OUT_FILE = Path("data/predictions/world_cup_brackets_v1.csv")


def get_group_rankings(sim_df: pd.DataFrame) -> dict[str, dict[str, str]]:
    group_rankings: dict[str, dict[str, str]] = {}
    for group, gdf in sim_df.groupby("group"):
        gdf = gdf.sort_values("position")
        group_rankings[group] = {
            "winner": gdf[gdf["position"] == 1]["team"].iloc[0],
            "runner_up": gdf[gdf["position"] == 2]["team"].iloc[0],
        }
    return group_rankings


def get_best_thirds_pool(sim_df: pd.DataFrame) -> list[dict]:
    """Eight best third-place teams, ranked (same tie-break as group simulation)."""
    thirds = sim_df[(sim_df["position"] == 3) & (sim_df["advanced"] == True)].copy()
    thirds = thirds.sort_values(
        ["points", "gd", "gf", "team"],
        ascending=[False, False, False, True],
    )
    return [
        {
            "group": str(row["group"]),
            "team": str(row["team"]),
            "points": float(row["points"]),
            "gd": float(row["gd"]),
            "gf": float(row["gf"]),
        }
        for _, row in thirds.iterrows()
    ]


def resolve_slot(
    slot: str,
    group_rankings: dict[str, dict[str, str]],
    available_thirds: list[dict],
) -> str | None:
    slot = str(slot).strip()

    m = re.match(r"Winner Group ([A-L])", slot)
    if m:
        group = m.group(1)
        return group_rankings[group]["winner"]

    m = re.match(r"Runner-up Group ([A-L])", slot)
    if m:
        group = m.group(1)
        return group_rankings[group]["runner_up"]

    m = re.match(r"Best 3rd \(Groups ([A-L/]+)\)", slot)
    if m:
        allowed = set(m.group(1).split("/"))
        for idx, third in enumerate(available_thirds):
            if third["group"] in allowed:
                team = third["team"]
                del available_thirds[idx]
                return team
        # No eligible third from listed groups — use next remaining qualifier
        if available_thirds:
            team = available_thirds[0]["team"]
            del available_thirds[0]
            return team
        return None

    return None


def _r32_teams(sim_df: pd.DataFrame) -> list[str]:
    teams: list[str] = []
    for col in ("home_team", "away_team"):
        for val in sim_df[col]:
            if pd.notna(val) and str(val).strip():
                teams.append(str(val))
    return teams


def count_r32_duplicate_sims(brackets: pd.DataFrame) -> tuple[int, int]:
    r32 = brackets[brackets["round"] == "Round of 32"]
    n_sims = int(r32["simulation_id"].nunique())
    dupes = 0
    for _, sim_df in r32.groupby("simulation_id"):
        teams = _r32_teams(sim_df)
        if len(teams) != len(set(teams)):
            dupes += 1
    return dupes, n_sims


def count_r32_valid_sims(brackets: pd.DataFrame) -> tuple[int, int]:
    r32 = brackets[brackets["round"] == "Round of 32"]
    n_sims = int(r32["simulation_id"].nunique())
    valid = 0
    for _, sim_df in r32.groupby("simulation_id"):
        teams = _r32_teams(sim_df)
        if len(teams) == 32 and len(set(teams)) == 32:
            valid += 1
    return valid, n_sims


def build_simulation_bracket(
    sim_df: pd.DataFrame,
    r32_slots: pd.DataFrame,
) -> list[dict]:
    group_rankings = get_group_rankings(sim_df)
    available_thirds = get_best_thirds_pool(sim_df)

    rows: list[dict] = []
    for _, match in r32_slots.sort_values("match_id").iterrows():
        home_team = resolve_slot(match["slot_home"], group_rankings, available_thirds)
        away_team = resolve_slot(match["slot_away"], group_rankings, available_thirds)
        rows.append(
            {
                "match_id": int(match["match_id"]),
                "round": match["round"],
                "date_utc": match["date_utc"],
                "venue": match["venue"],
                "slot_home": match["slot_home"],
                "slot_away": match["slot_away"],
                "home_team": home_team,
                "away_team": away_team,
            }
        )
    return rows


def main():
    rankings = pd.read_csv(RANKINGS_FILE)
    slots = pd.read_csv(SLOTS_FILE)
    r32 = slots[slots["round"] == "Round of 32"].copy()

    if OUT_FILE.exists():
        before_dupes, before_n = count_r32_duplicate_sims(pd.read_csv(OUT_FILE))
        print(f"Before fix: R32 duplicate-team simulations {before_dupes:,} / {before_n:,}")
    else:
        print("Before fix: (no existing bracket file)")

    rows = []
    for sim_id, sim_df in rankings.groupby("simulation_id"):
        sim_rows = build_simulation_bracket(sim_df, r32)
        for rec in sim_rows:
            rec["simulation_id"] = int(sim_id)
            rows.append(rec)

    out = pd.DataFrame(rows)

    unresolved = out[out["home_team"].isna() | out["away_team"].isna()]
    after_dupes, after_n = count_r32_duplicate_sims(out)
    after_valid, _ = count_r32_valid_sims(out)

    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Rows: {len(out):,}")
    print(f"Unresolved rows: {len(unresolved):,}")
    print(f"After fix: R32 duplicate-team simulations {after_dupes:,} / {after_n:,}")
    print(f"After fix: fully valid R32 (32 unique teams) {after_valid:,} / {after_n:,}")

    if len(unresolved) > 0:
        print("\nUnresolved sample:")
        print(unresolved.head(20))

    if after_dupes > 0:
        print("\nWARNING: some simulations still have duplicate R32 teams.")
        bad = []
        for sim_id, sim_df in out.groupby("simulation_id"):
            teams = list(sim_df["home_team"]) + list(sim_df["away_team"])
            if len(teams) != len(set(teams)):
                bad.append(int(sim_id))
                if len(bad) >= 5:
                    break
        print(f"Sample simulation_ids: {bad}")

    print("\nPreview (simulation_id=1):")
    print(
        out[out["simulation_id"] == 1][
            ["match_id", "home_team", "away_team"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
