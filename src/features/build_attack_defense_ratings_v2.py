from pathlib import Path
import pandas as pd
import numpy as np

MATCH_FILE = Path(
    "data/processed/match_training_fifa_only.csv"
)
OUT_DIR = Path("data/features")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "team_attack_defense_v2.csv"


def build_team_rows(matches: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, r in matches.iterrows():
        rows.append({
            "date": r["date"],
            "team": r["home_team"],
            "opponent": r["away_team"],
            "goals_for": r["home_score"],
            "goals_against": r["away_score"],
            "is_home": 1,
            "is_neutral": int(bool(r["neutral"])),
            "tournament": r["tournament"],
        })

        rows.append({
            "date": r["date"],
            "team": r["away_team"],
            "opponent": r["home_team"],
            "goals_for": r["away_score"],
            "goals_against": r["home_score"],
            "is_home": 0,
            "is_neutral": int(bool(r["neutral"])),
            "tournament": r["tournament"],
        })

    return pd.DataFrame(rows)


def weighted_average(values, weights):
    values = np.array(values, dtype=float)
    weights = np.array(weights, dtype=float)

    if len(values) == 0 or weights.sum() == 0:
        return np.nan

    return np.average(values, weights=weights)


def tournament_weight(tournament: str) -> float:
    important = {
        "FIFA World Cup": 1.50,
        "UEFA Euro": 1.35,
        "Copa América": 1.35,
        "AFC Asian Cup": 1.20,
        "Africa Cup of Nations": 1.20,
        "CONCACAF Gold Cup": 1.20,
        "FIFA World Cup qualification": 1.15,
        "UEFA Nations League": 1.10,
    }
    return important.get(tournament, 1.0)


def main():
    matches = pd.read_csv(MATCH_FILE)
    matches["date"] = pd.to_datetime(matches["date"])

    team_rows = build_team_rows(matches)
    team_rows["date"] = pd.to_datetime(team_rows["date"])

    latest_date = team_rows["date"].max()
    team_rows["days_ago"] = (latest_date - team_rows["date"]).dt.days


    team_rows["time_weight"] = np.exp(-team_rows["days_ago"] / 3650)


    team_rows["tournament_weight"] = team_rows["tournament"].apply(tournament_weight)

    team_rows["final_weight"] = team_rows["time_weight"] * team_rows["tournament_weight"]

    global_avg_goals_for = weighted_average(
        team_rows["goals_for"],
        team_rows["final_weight"]
    )

    rows = []

    for team, df in team_rows.groupby("team"):
        df = df.sort_values("date")

        last_10 = df.tail(10)
        last_20 = df.tail(20)
        last_50 = df.tail(50)

        weighted_gf = weighted_average(df["goals_for"], df["final_weight"])
        weighted_ga = weighted_average(df["goals_against"], df["final_weight"])

        attack_rating = weighted_gf / global_avg_goals_for
        defense_rating = weighted_ga / global_avg_goals_for

        rows.append({
            "team": team,
            "matches": len(df),
            "weighted_goals_for": weighted_gf,
            "weighted_goals_against": weighted_ga,
            "attack_rating": attack_rating,
            "defense_rating": defense_rating,

            "last_10_goals_for": last_10["goals_for"].mean(),
            "last_10_goals_against": last_10["goals_against"].mean(),
            "last_20_goals_for": last_20["goals_for"].mean(),
            "last_20_goals_against": last_20["goals_against"].mean(),
            "last_50_goals_for": last_50["goals_for"].mean(),
            "last_50_goals_against": last_50["goals_against"].mean(),

            "last_match_date": df["date"].max(),
        })

    ratings = pd.DataFrame(rows)

    ratings["attack_rating"] = ratings["attack_rating"].clip(0.35, 2.50)
    ratings["defense_rating"] = ratings["defense_rating"].clip(0.35, 2.50)

    ratings["net_rating"] = ratings["attack_rating"] - ratings["defense_rating"]

    ratings = ratings.sort_values("net_rating", ascending=False)

    ratings.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Teams: {len(ratings)}")

    print("\nTop 30 by net_rating:")
    print(
        ratings[
            [
                "team",
                "matches",
                "attack_rating",
                "defense_rating",
                "net_rating",
                "last_10_goals_for",
                "last_10_goals_against",
            ]
        ].head(30)
    )


if __name__ == "__main__":
    main()