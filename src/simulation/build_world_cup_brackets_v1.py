from pathlib import Path
import re
import pandas as pd

RANKINGS_FILE = Path("data/predictions/group_stage_rankings_v3.csv")
SLOTS_FILE = Path("data/raw/knockout_slots.csv")
OUT_FILE = Path("data/predictions/world_cup_brackets_v1.csv")


def get_group_rankings(sim_df):
    group_rankings = {}

    for group, gdf in sim_df.groupby("group"):
        gdf = gdf.sort_values("position")

        group_rankings[group] = {
            "winner": gdf[gdf["position"] == 1]["team"].iloc[0],
            "runner_up": gdf[gdf["position"] == 2]["team"].iloc[0],
        }

    return group_rankings


def get_best_thirds(sim_df):
    thirds = sim_df[
        (sim_df["position"] == 3) & (sim_df["advanced"] == True)
    ].copy()

    best_thirds = {}
    for _, row in thirds.iterrows():
        best_thirds[row["group"]] = row["team"]

    return best_thirds


def resolve_slot(slot, group_rankings, best_thirds):
    slot = str(slot).strip()

    # Winner Group A
    m = re.match(r"Winner Group ([A-L])", slot)
    if m:
        group = m.group(1)
        return group_rankings[group]["winner"]

    # Runner-up Group B
    m = re.match(r"Runner-up Group ([A-L])", slot)
    if m:
        group = m.group(1)
        return group_rankings[group]["runner_up"]

    # Best 3rd (Groups C/E/F/H/I/J)
    m = re.match(r"Best 3rd \(Groups ([A-L/]+)\)", slot)
    if m:
        candidate_groups = m.group(1).split("/")

        for g in candidate_groups:
            if g in best_thirds:
                return best_thirds[g]

        return None

    return None


def main():
    rankings = pd.read_csv(RANKINGS_FILE)
    slots = pd.read_csv(SLOTS_FILE)

    r32 = slots[slots["round"] == "Round of 32"].copy()

    rows = []

    for sim_id, sim_df in rankings.groupby("simulation_id"):
        group_rankings = get_group_rankings(sim_df)
        best_thirds = get_best_thirds(sim_df)

        for _, match in r32.iterrows():
            home_team = resolve_slot(
                match["slot_home"],
                group_rankings,
                best_thirds
            )

            away_team = resolve_slot(
                match["slot_away"],
                group_rankings,
                best_thirds
            )

            rows.append({
                "simulation_id": sim_id,
                "match_id": match["match_id"],
                "round": match["round"],
                "date_utc": match["date_utc"],
                "venue": match["venue"],
                "slot_home": match["slot_home"],
                "slot_away": match["slot_away"],
                "home_team": home_team,
                "away_team": away_team,
            })

    out = pd.DataFrame(rows)

    unresolved = out[
        out["home_team"].isna() | out["away_team"].isna()
    ]

    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Rows: {len(out):,}")
    print(f"Unresolved rows: {len(unresolved):,}")

    if len(unresolved) > 0:
        print("\nUnresolved sample:")
        print(unresolved.head(20))

    print("\nPreview:")
    print(out.head(32))


if __name__ == "__main__":
    main()