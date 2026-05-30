from __future__ import annotations
import numpy as np
import pandas as pd
from src.models.poisson_model import PoissonScoreModel


def predict_match_row(row: pd.Series, model: PoissonScoreModel, knockout: bool = False) -> dict:
    hg, ag, p = model.most_likely_score(row.home_rating, row.away_rating, neutral=True)
    probs = model.outcome_probs(row.home_rating, row.away_rating, neutral=True)
    if knockout and hg == ag:
        winner = "home" if probs["home"] >= probs["away"] else "away"
        penalties = True
    else:
        winner = "home" if hg > ag else "away" if ag > hg else "draw"
        penalties = False
    # Conservative defaults: total corners/cards are count predictions for the match.
    # Phase 2 will replace this with count models.
    rating_gap = abs(row.home_rating - row.away_rating)
    corners = int(np.clip(round(9.2 + min(rating_gap, 350) / 350 * 0.8), 7, 12))
    yellow_cards = int(np.clip(round(3.6 + (1 if knockout else 0)), 2, 7))
    red_cards = 0
    return {
        "predicted_home_goals": hg,
        "predicted_away_goals": ag,
        "corners": corners,
        "yellow_cards": yellow_cards,
        "red_cards": red_cards,
        "winner": winner,
        "penalties": penalties,
        "score_probability": p,
        "home_win_probability": probs["home"],
        "draw_probability": probs["draw"],
        "away_win_probability": probs["away"],
    }
