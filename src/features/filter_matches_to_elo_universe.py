from pathlib import Path
import pandas as pd

MATCH_FILE = Path("data/processed/match_training_table.csv")
ELO_FILE = Path("data/raw/official_elo/eloratings.csv")
OUT_FILE = Path("data/processed/match_training_fifa_only.csv")

def main():
    matches = pd.read_csv(MATCH_FILE)
    elo = pd.read_csv(ELO_FILE)

    valid_teams = set(elo["team"].dropna().unique())

    filtered = matches[
        matches["home_team"].isin(valid_teams)
        & matches["away_team"].isin(valid_teams)
    ].copy()

    filtered.to_csv(OUT_FILE, index=False)

    print(f"Original matches: {len(matches):,}")
    print(f"Filtered matches: {len(filtered):,}")
    print(f"Valid teams: {len(valid_teams):,}")
    print(f"Saved {OUT_FILE}")

    removed_teams = (
        set(matches["home_team"]).union(set(matches["away_team"]))
        - valid_teams
    )
    print("\nExample removed teams:")
    print(sorted(list(removed_teams))[:60])

if __name__ == "__main__":
    main()