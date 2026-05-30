from __future__ import annotations
import pandas as pd

# Curated Phase-1 priors. Replace/overwrite with live Elo + FIFA ranking in Phase 2.
# Scale is Elo-like: elite ~2050+, strong ~1900, average ~1650, weaker ~1400.
TEAM_STRENGTH_PRIORS = {
    "Argentina": 2075, "France": 2070, "Spain": 2050, "England": 2025, "Brazil": 2015,
    "Portugal": 1995, "Netherlands": 1960, "Germany": 1945, "Uruguay": 1915, "Croatia": 1890,
    "Belgium": 1885, "Colombia": 1870, "Morocco": 1855, "USA": 1815, "Japan": 1810,
    "Switzerland": 1805, "Austria": 1795, "Ecuador": 1785, "Senegal": 1775, "Mexico": 1765,
    "Paraguay": 1740, "Iran": 1730, "South Korea": 1725, "Australia": 1715, "Norway": 1710,
    "Côte d'Ivoire": 1695, "Canada": 1685, "Scotland": 1680, "Egypt": 1675, "Algeria": 1665,
    "Qatar": 1605, "Tunisia": 1600, "South Africa": 1585, "Saudi Arabia": 1580, "Ghana": 1575,
    "Uzbekistan": 1565, "Panama": 1545, "New Zealand": 1535, "Jordan": 1510, "Haiti": 1495,
    "Curaçao": 1485, "Cabo Verde": 1480,
    "UEFA Playoff A": 1680, "UEFA Playoff B": 1660, "UEFA Playoff C": 1650, "UEFA Playoff D": 1640,
    "FIFA Playoff 1": 1540, "FIFA Playoff 2": 1540,
}


def build_team_strength_table(teams: list[str]) -> pd.DataFrame:
    rows = []
    for team in sorted(set(teams)):
        rating = TEAM_STRENGTH_PRIORS.get(team, 1600)
        rows.append({"team": team, "rating": rating, "rating_source": "phase1_curated_prior"})
    return pd.DataFrame(rows)


def save_team_strength_table(teams: list[str], path: str) -> pd.DataFrame:
    df = build_team_strength_table(teams)
    df.to_csv(path, index=False)
    return df
