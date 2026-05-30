from pathlib import Path
import pandas as pd

MATCH_FILE = Path("data/processed/match_training_table.csv")
OUT_FILE = Path("configs/world_cup_candidate_teams.csv")

df = pd.read_csv(MATCH_FILE)

teams = set(df["home_team"]).union(set(df["away_team"]))


team_df = pd.DataFrame({
    "team": sorted(list(teams))
})

team_df.to_csv(OUT_FILE, index=False)

print(f"Saved {OUT_FILE}")
print(f"Teams: {len(team_df)}")