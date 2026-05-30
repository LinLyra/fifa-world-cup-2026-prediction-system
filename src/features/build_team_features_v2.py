from pathlib import Path
import pandas as pd
import numpy as np

MATCH_FILE = Path(
    "data/processed/match_training_fifa_only.csv"
)

ELO_FILE = Path(
    "data/processed/current_elo_v2.csv"
)

OUT_DIR = Path("data/features")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def points_for(team_goals, opponent_goals):
    if team_goals > opponent_goals:
        return 3
    if team_goals == opponent_goals:
        return 1
    return 0


def build_team_match_rows(matches: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, r in matches.iterrows():
        rows.append({
            "date": r["date"],
            "team": r["home_team"],
            "opponent": r["away_team"],
            "goals_for": r["home_score"],
            "goals_against": r["away_score"],
            "goal_diff": r["home_score"] - r["away_score"],
            "points": points_for(r["home_score"], r["away_score"]),
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
            "goal_diff": r["away_score"] - r["home_score"],
            "points": points_for(r["away_score"], r["home_score"]),
            "is_home": 0,
            "is_neutral": int(bool(r["neutral"])),
            "tournament": r["tournament"],
        })

    return pd.DataFrame(rows)


def recent_features(team_df: pd.DataFrame, n: int) -> dict:
    recent = team_df.sort_values("date").tail(n)

    if len(recent) == 0:
        return {
            f"last_{n}_matches": 0,
            f"last_{n}_points_per_game": np.nan,
            f"last_{n}_goals_for_per_game": np.nan,
            f"last_{n}_goals_against_per_game": np.nan,
            f"last_{n}_goal_diff_per_game": np.nan,
            f"last_{n}_win_rate": np.nan,
            f"last_{n}_clean_sheet_rate": np.nan,
            f"last_{n}_failed_to_score_rate": np.nan,
        }

    return {
        f"last_{n}_matches": len(recent),
        f"last_{n}_points_per_game": recent["points"].mean(),
        f"last_{n}_goals_for_per_game": recent["goals_for"].mean(),
        f"last_{n}_goals_against_per_game": recent["goals_against"].mean(),
        f"last_{n}_goal_diff_per_game": recent["goal_diff"].mean(),
        f"last_{n}_win_rate": (recent["points"] == 3).mean(),
        f"last_{n}_clean_sheet_rate": (recent["goals_against"] == 0).mean(),
        f"last_{n}_failed_to_score_rate": (recent["goals_for"] == 0).mean(),
    }


def main():
    matches = pd.read_csv(MATCH_FILE)
    matches["date"] = pd.to_datetime(matches["date"])

    elo = pd.read_csv(ELO_FILE)

    team_rows = build_team_match_rows(matches)
    team_rows = team_rows.sort_values(["team", "date"])

    feature_rows = []

    for team, team_df in team_rows.groupby("team"):
        team_df = team_df.sort_values("date")

        row = {
            "team": team,
            "matches_played": len(team_df),
            "first_match_date": team_df["date"].min(),
            "last_match_date": team_df["date"].max(),
            "career_points_per_game": team_df["points"].mean(),
            "career_goals_for_per_game": team_df["goals_for"].mean(),
            "career_goals_against_per_game": team_df["goals_against"].mean(),
            "career_goal_diff_per_game": team_df["goal_diff"].mean(),
            "career_win_rate": (team_df["points"] == 3).mean(),
            "career_clean_sheet_rate": (team_df["goals_against"] == 0).mean(),
        }

        for n in [5, 10, 20, 50]:
            row.update(recent_features(team_df, n))

        feature_rows.append(row)

    features = pd.DataFrame(feature_rows)

    features = features.merge(
        elo.rename(columns={"elo": "custom_elo"}),
        on="team",
        how="left"
    )

    features["custom_elo"] = features["custom_elo"].fillna(1500)

    
    features["strength_score_v1"] = (
        0.45 * features["custom_elo"]
        + 120 * features["last_10_points_per_game"].fillna(features["career_points_per_game"])
        + 80 * features["last_20_goal_diff_per_game"].fillna(features["career_goal_diff_per_game"])
        - 60 * features["last_10_goals_against_per_game"].fillna(features["career_goals_against_per_game"])
    )

    features = features.sort_values("strength_score_v1", ascending=False)

    out = OUT_DIR / "team_features_v2.csv"
    features.to_csv(out, index=False)

    print(f"Saved {out}")
    print(f"Teams: {len(features):,}")
    print("\nTop 20 by strength_score_v1:")
    print(features[[
        "team",
        "custom_elo",
        "last_10_points_per_game",
        "last_10_goals_for_per_game",
        "last_10_goals_against_per_game",
        "strength_score_v1"
    ]].head(20))


if __name__ == "__main__":
    main()