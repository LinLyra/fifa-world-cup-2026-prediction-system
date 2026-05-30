from pathlib import Path
import pandas as pd
import numpy as np

PRED_FILE = Path(
    "data/predictions/dixon_coles_group_predictions_v1.csv"
)

OUT_FILE = Path(
    "data/predictions/group_stage_simulation_v1.csv"
)

N_SIM = 10000


def simulate_match(row):
    probs = [
        row["home_win_prob"],
        row["draw_prob"],
        row["away_win_prob"],
    ]

    outcome = np.random.choice(
        ["H", "D", "A"],
        p=probs
    )

    return outcome


def main():
    df = pd.read_csv(PRED_FILE)

    teams = sorted(
        set(df["home_team"]).union(
            set(df["away_team"])
        )
    )

    advance_counts = {
        team: 0
        for team in teams
    }

    for sim in range(N_SIM):

        table = {
            team: 0
            for team in teams
        }

        for _, row in df.iterrows():

            result = simulate_match(row)

            home = row["home_team"]
            away = row["away_team"]

            if result == "H":
                table[home] += 3

            elif result == "A":
                table[away] += 3

            else:
                table[home] += 1
                table[away] += 1

        ranking = sorted(
            table.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_half = ranking[: len(ranking)//2]

        for team, _ in top_half:
            advance_counts[team] += 1

    out = pd.DataFrame({
        "team": list(advance_counts.keys()),
        "advance_probability": [
            advance_counts[t]/N_SIM
            for t in advance_counts
        ]
    })

    out = out.sort_values(
        "advance_probability",
        ascending=False
    )

    out.to_csv(
        OUT_FILE,
        index=False
    )

    print(
        f"Saved {OUT_FILE}"
    )

    print(
        out.head(30)
    )


if __name__ == "__main__":
    main()