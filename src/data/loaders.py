from __future__ import annotations
from pathlib import Path
import pandas as pd


def load_group_fixtures(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"match_id", "group", "home_team", "away_team", "date_utc", "venue"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"group_fixtures missing columns: {missing}")
    return df


def load_knockout_slots(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"match_id", "round", "multiplier", "date_utc", "venue", "slot_home", "slot_away"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"knockout_slots missing columns: {missing}")
    return df
