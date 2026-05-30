"""
Phase-2 data connector stubs.

These functions are intentionally conservative. Do not scrape aggressively.
Prefer official APIs, downloadable CSVs, or manual snapshots for competition work.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd


def load_historical_results_csv(path: str | Path) -> pd.DataFrame:
    """Load a historical international-results CSV once downloaded manually."""
    df = pd.read_csv(path)
    expected_any = [{"date", "home_team", "away_team", "home_score", "away_score"}]
    if not any(cols.issubset(df.columns) for cols in expected_any):
        raise ValueError("Historical results CSV needs date/home_team/away_team/home_score/away_score columns")
    return df


def load_odds_snapshot_csv(path: str | Path) -> pd.DataFrame:
    """Load bookmaker odds snapshot. Use for market calibration in Phase 3."""
    return pd.read_csv(path)


def load_squad_news_snapshot_csv(path: str | Path) -> pd.DataFrame:
    """Load curated injury/squad/news features. Avoid LLM-only unverified news scoring."""
    return pd.read_csv(path)
