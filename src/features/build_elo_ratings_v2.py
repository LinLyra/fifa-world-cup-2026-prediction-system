from pathlib import Path
import pandas as pd
import numpy as np

RAW_FILE = Path("data/processed/match_training_fifa_only.csv")

PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(exist_ok=True)

BASE_ELO = 1500

TOURNAMENT_WEIGHTS = {
    "FIFA World Cup": 60,
    "UEFA Euro": 50,
    "Copa América": 50,
    "AFC Asian Cup": 40,
    "Africa Cup of Nations": 40,
    "CONCACAF Gold Cup": 40,
    "UEFA Nations League": 35,
    "FIFA World Cup qualification": 30,
}

DEFAULT_K = 20


def get_k_factor(tournament):
    return TOURNAMENT_WEIGHTS.get(tournament, DEFAULT_K)


def expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def main():

    df = pd.read_csv(RAW_FILE)
    df["date"] = pd.to_datetime(df["date"])

    ratings = {}

    history = []

    for _, row in df.iterrows():

        home = row["home_team"]
        away = row["away_team"]

        home_rating = ratings.get(home, BASE_ELO)
        away_rating = ratings.get(away, BASE_ELO)

        exp_home = expected_score(home_rating, away_rating)
        exp_away = expected_score(away_rating, home_rating)

        if row["home_score"] > row["away_score"]:
            score_home = 1
            score_away = 0

        elif row["home_score"] < row["away_score"]:
            score_home = 0
            score_away = 1

        else:
            score_home = 0.5
            score_away = 0.5

        k = get_k_factor(row["tournament"])

        new_home = home_rating + k * (score_home - exp_home)
        new_away = away_rating + k * (score_away - exp_away)

        ratings[home] = new_home
        ratings[away] = new_away

        history.append({
            "date": row["date"],
            "home_team": home,
            "away_team": away,
            "home_elo_before": home_rating,
            "away_elo_before": away_rating,
            "home_elo_after": new_home,
            "away_elo_after": new_away,
        })

    elo_history = pd.DataFrame(history)

    current_elo = (
        pd.DataFrame(
            [{"team": k, "elo": v} for k, v in ratings.items()]
        )
        .sort_values("elo", ascending=False)
        .reset_index(drop=True)
    )

    elo_history.to_csv(
        PROCESSED_DIR / "elo_history_v2.csv",
        index=False
    )

    current_elo.to_csv(
        PROCESSED_DIR / "current_elo_v2.csv",
        index=False
    )

    print("\nTop 20 Teams:\n")
    print(current_elo.head(20))

    print("\nSaved:")
    print("elo_history_v2.csv")
    print("current_elo_v2.csv")


if __name__ == "__main__":
    main()