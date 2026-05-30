from __future__ import annotations
import re
import numpy as np
import pandas as pd
from src.models.poisson_model import PoissonScoreModel
from src.features.basic_features import add_rating_features
from src.submission.prediction_utils import predict_match_row


def _rank_group(table: pd.DataFrame) -> pd.DataFrame:
    return table.sort_values(
        ["points", "goal_diff", "goals_for", "team"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)


def predict_group_stage(group_fixtures: pd.DataFrame, ratings: pd.DataFrame, model: PoissonScoreModel):
    fixtures = add_rating_features(group_fixtures, ratings)
    predictions = []
    standings = []
    for _, row in fixtures.iterrows():
        pred = predict_match_row(row, model, knockout=False)
        rec = row.to_dict()
        rec.update({k: v for k, v in pred.items() if k != "winner"})
        rec["winning_team"] = pred["winner"]
        predictions.append(rec)

    pred_df = pd.DataFrame(predictions)
    for group, g in pred_df.groupby("group"):
        teams = sorted(set(g.home_team) | set(g.away_team))
        table = {t: {"team": t, "group": group, "points": 0, "goals_for": 0, "goals_against": 0, "goal_diff": 0} for t in teams}
        for _, m in g.iterrows():
            h, a = m.home_team, m.away_team
            hg, ag = int(m.predicted_home_goals), int(m.predicted_away_goals)
            table[h]["goals_for"] += hg; table[h]["goals_against"] += ag
            table[a]["goals_for"] += ag; table[a]["goals_against"] += hg
            if hg > ag:
                table[h]["points"] += 3
            elif ag > hg:
                table[a]["points"] += 3
            else:
                table[h]["points"] += 1; table[a]["points"] += 1
        df = pd.DataFrame(table.values())
        df["goal_diff"] = df.goals_for - df.goals_against
        ranked = _rank_group(df)
        ranked["rank"] = np.arange(1, len(ranked) + 1)
        standings.append(ranked)
    return pred_df, pd.concat(standings, ignore_index=True)


def build_slot_map(standings: pd.DataFrame) -> tuple[dict[str, str], list[dict]]:
    slots: dict[str, str] = {}
    thirds = []
    for group, g in standings.groupby("group"):
        ranked = g.sort_values("rank")
        slots[f"Winner Group {group}"] = ranked.iloc[0].team
        slots[f"Runner-up Group {group}"] = ranked.iloc[1].team
        third = ranked.iloc[2].to_dict()
        thirds.append(third)
    thirds_sorted = sorted(thirds, key=lambda x: (x["points"], x["goal_diff"], x["goals_for"], x["team"]), reverse=True)
    return slots, thirds_sorted[:8]


def resolve_slot(slot: str, slot_map: dict[str, str], available_thirds: list[dict]) -> str:
    if slot in slot_map:
        return slot_map[slot]
    m = re.match(r"Best 3rd \(Groups ([A-L/]+)\)", slot)
    if m:
        allowed = set(m.group(1).split("/"))
        for idx, third in enumerate(available_thirds):
            if third["group"] in allowed:
                team = third["team"]
                del available_thirds[idx]
                return team
        # fallback if the predetermined slot is inconsistent with our simple ranking
        for idx, third in enumerate(available_thirds):
            team = third["team"]
            del available_thirds[idx]
            return team
    m = re.match(r"Winner Match (\d+)", slot)
    if m:
        return slot_map[f"Winner Match {m.group(1)}"]
    m = re.match(r"Loser Match (\d+)", slot)
    if m:
        return slot_map[f"Loser Match {m.group(1)}"]
    raise ValueError(f"Cannot resolve slot: {slot}")


def predict_knockouts(knockout_slots: pd.DataFrame, ratings: pd.DataFrame, standings: pd.DataFrame, model: PoissonScoreModel):
    rating_map = ratings.set_index("team")["rating"].to_dict()
    slot_map, best_thirds = build_slot_map(standings)
    available_thirds = [dict(x) for x in best_thirds]
    rows = []
    for _, slot in knockout_slots.sort_values("match_id").iterrows():
        home = resolve_slot(slot.slot_home, slot_map, available_thirds)
        away = resolve_slot(slot.slot_away, slot_map, available_thirds)
        row = pd.Series({
            "home_team": home, "away_team": away,
            "home_rating": rating_map.get(home, 1600), "away_rating": rating_map.get(away, 1600)
        })
        pred = predict_match_row(row, model, knockout=True)
        # If draw in knockout, keep draw scoreline and choose penalty winner.
        winner_team = home if pred["winner"] == "home" else away
        loser_team = away if pred["winner"] == "home" else home
        slot_map[f"Winner Match {int(slot.match_id)}"] = winner_team
        slot_map[f"Loser Match {int(slot.match_id)}"] = loser_team
        rec = slot.to_dict()
        rec.update({
            "predicted_home_team": home,
            "predicted_away_team": away,
            "predicted_home_goals": pred["predicted_home_goals"],
            "predicted_away_goals": pred["predicted_away_goals"],
            "corners": pred["corners"],
            "yellow_cards": pred["yellow_cards"],
            "red_cards": pred["red_cards"],
            "match_winner": pred["winner"],
            "penalties": pred["penalties"],
            "score_probability": pred["score_probability"],
            "home_win_probability": pred["home_win_probability"],
            "draw_probability": pred["draw_probability"],
            "away_win_probability": pred["away_win_probability"],
        })
        rows.append(rec)
    return pd.DataFrame(rows)


def tournament_summary(group_predictions: pd.DataFrame, knockout_predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # deterministic baseline summary: teams appearing in each final predicted stage
    for _, row in knockout_predictions.iterrows():
        for side in ["home", "away"]:
            rows.append({"team": row[f"predicted_{side}_team"], "round": row["round"], "match_id": row["match_id"]})
    return pd.DataFrame(rows)
