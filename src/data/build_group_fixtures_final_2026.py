from pathlib import Path
import pandas as pd
from itertools import combinations

OUT_FILE = Path("data/raw/group_fixtures_final.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

rows = []
match_id = 1

for group, teams in GROUPS.items():
    for home, away in combinations(teams, 2):
        rows.append({
            "match_id": match_id,
            "group": group,
            "home_team": home,
            "away_team": away,
            "date_utc": "",
            "venue": "",
        })
        match_id += 1

df = pd.DataFrame(rows)
df.to_csv(OUT_FILE, index=False)

print(f"Saved {OUT_FILE}")
print(f"Rows: {len(df)}")
print(df.head(20))