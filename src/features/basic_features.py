from __future__ import annotations
import pandas as pd


def add_rating_features(fixtures: pd.DataFrame, ratings: pd.DataFrame) -> pd.DataFrame:
    r = ratings.set_index("team")["rating"].to_dict()
    out = fixtures.copy()
    out["home_rating"] = out["home_team"].map(r).fillna(1600)
    out["away_rating"] = out["away_team"].map(r).fillna(1600)
    out["rating_diff"] = out["home_rating"] - out["away_rating"]
    return out
