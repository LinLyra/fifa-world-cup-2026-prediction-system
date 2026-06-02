from pathlib import Path
import pandas as pd
import numpy as np

BRACKET_FILE = Path(
    "data/predictions/world_cup_brackets_v1.csv"
)

MATCH_FILE = Path(
    "data/predictions/match_strength_matrix_v2.csv"
)

OUT_FILE = Path(
    "data/predictions/world_cup_champion_probabilities_v2.csv"
)

def build_match_lookup(df):
    lookup = {}

    for _, row in df.iterrows():
        lookup[
            (row["home_team"], row["away_team"])
        ] = (
            row["home_win_prob"],
            row["draw_prob"],
            row["away_win_prob"]
        )

    return lookup


def simulate_match(team_a, team_b, lookup):
    if (team_a, team_b) in lookup:
        hw, dr, aw = lookup[(team_a, team_b)]

    elif (team_b, team_a) in lookup:
        aw, dr, hw = lookup[(team_b, team_a)]

    else:
        return np.random.choice([team_a, team_b])

    p_a = hw + dr * 0.5
    p_b = aw + dr * 0.5

    total = p_a + p_b

    p_a /= total
    p_b /= total

    return np.random.choice(
        [team_a, team_b],
        p=[p_a, p_b]
    )


def main():

    bracket = pd.read_csv(BRACKET_FILE)

    match_lookup = build_match_lookup(
        pd.read_csv(MATCH_FILE)
    )

    champion_counts = {}

    simulations = bracket["simulation_id"].nunique()

    for sim_id, sim_df in bracket.groupby("simulation_id"):

        winners = {}

        # Round of 32
        for _, row in sim_df.iterrows():

            winner = simulate_match(
                row["home_team"],
                row["away_team"],
                match_lookup
            )

            winners[row["match_id"]] = winner

        # Round of 16
        winners[89] = simulate_match(
            winners[73],
            winners[77],
            match_lookup
        )

        winners[90] = simulate_match(
            winners[74],
            winners[78],
            match_lookup
        )

        winners[91] = simulate_match(
            winners[76],
            winners[80],
            match_lookup
        )

        winners[92] = simulate_match(
            winners[79],
            winners[83],
            match_lookup
        )

        winners[93] = simulate_match(
            winners[81],
            winners[84],
            match_lookup
        )

        winners[94] = simulate_match(
            winners[82],
            winners[85],
            match_lookup
        )

        winners[95] = simulate_match(
            winners[86],
            winners[87],
            match_lookup
        )

        winners[96] = simulate_match(
            winners[88],
            winners[75],
            match_lookup
        )

        # Quarterfinals

        winners[97] = simulate_match(
            winners[89],
            winners[90],
            match_lookup
        )

        winners[98] = simulate_match(
            winners[91],
            winners[92],
            match_lookup
        )

        winners[99] = simulate_match(
            winners[93],
            winners[94],
            match_lookup
        )

        winners[100] = simulate_match(
            winners[95],
            winners[96],
            match_lookup
        )

        # Semifinals

        winners[101] = simulate_match(
            winners[97],
            winners[98],
            match_lookup
        )

        winners[102] = simulate_match(
            winners[99],
            winners[100],
            match_lookup
        )

        # Final

        champion = simulate_match(
            winners[101],
            winners[102],
            match_lookup
        )

        champion_counts[champion] = (
            champion_counts.get(champion, 0) + 1
        )

    out = pd.DataFrame([
        {
            "team": team,
            "champion_prob": count / simulations,
            "titles": count
        }
        for team, count in champion_counts.items()
    ])

    out = out.sort_values(
        "champion_prob",
        ascending=False
    )

    out.to_csv(
        OUT_FILE,
        index=False
    )

    print(f"Saved {OUT_FILE}")

    print("\nTop 40 Champions:")

    print(
        out.head(40)
    )


if __name__ == "__main__":
    main()