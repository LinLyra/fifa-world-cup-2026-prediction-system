from __future__ import annotations
from pathlib import Path
import pandas as pd

from src.data.loaders import load_group_fixtures, load_knockout_slots
from src.models.team_priors import save_team_strength_table
from src.models.poisson_model import PoissonScoreModel, PoissonConfig
from src.simulation.tournament import predict_group_stage, predict_knockouts, tournament_summary

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "predictions"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    group_fixtures = load_group_fixtures(RAW / "group_fixtures.csv")
    knockout_slots = load_knockout_slots(RAW / "knockout_slots.csv")
    teams = sorted(set(group_fixtures.home_team) | set(group_fixtures.away_team))
    ratings = save_team_strength_table(teams, OUT / "team_strength_priors.csv")

    model = PoissonScoreModel(PoissonConfig(max_goals=7))

    group_predictions, standings = predict_group_stage(group_fixtures, ratings, model)
    knockout_predictions = predict_knockouts(knockout_slots, ratings, standings, model)
    summary = tournament_summary(group_predictions, knockout_predictions)

    # DataCamp-compatible core outputs
    group_cols = list(group_fixtures.columns) + [
        "predicted_home_goals", "predicted_away_goals", "corners",
        "yellow_cards", "red_cards", "winning_team"
    ]
    knockout_cols = list(knockout_slots.columns) + [
        "predicted_home_team", "predicted_away_team", "predicted_home_goals",
        "predicted_away_goals", "corners", "yellow_cards", "red_cards",
        "match_winner", "penalties"
    ]
    group_predictions[group_cols].to_csv(OUT / "group_predictions.csv", index=False)
    knockout_predictions[knockout_cols].to_csv(OUT / "knockout_predictions.csv", index=False)

    all_predictions = pd.concat([
        group_predictions.assign(stage="group"),
        knockout_predictions.assign(stage="knockout")
    ], ignore_index=True, sort=False)
    all_predictions.to_csv(OUT / "all_predictions.csv", index=False)
    standings.to_csv(OUT / "predicted_group_standings.csv", index=False)
    summary.to_csv(OUT / "tournament_summary.csv", index=False)

    print("Generated predictions:")
    print(f"- {OUT / 'group_predictions.csv'}")
    print(f"- {OUT / 'knockout_predictions.csv'}")
    print(f"- {OUT / 'all_predictions.csv'}")
    print("Predicted champion:", knockout_predictions.loc[knockout_predictions.match_id == 104, "predicted_home_team"].iloc[0]
          if knockout_predictions.loc[knockout_predictions.match_id == 104, "match_winner"].iloc[0] == "home"
          else knockout_predictions.loc[knockout_predictions.match_id == 104, "predicted_away_team"].iloc[0])


if __name__ == "__main__":
    main()
