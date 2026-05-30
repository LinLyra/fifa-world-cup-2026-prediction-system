from pathlib import Path
import pandas as pd
import numpy as np

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    df = pd.read_csv(RAW_DIR / "results.csv")
    df["date"] = pd.to_datetime(df["date"])

   
    df = df.dropna(subset=["home_team", "away_team", "home_score", "away_score"])
    df = df.sort_values("date").reset_index(drop=True)


    df["home_win"] = (df["home_score"] > df["away_score"]).astype(int)
    df["draw"] = (df["home_score"] == df["away_score"]).astype(int)
    df["away_win"] = (df["home_score"] < df["away_score"]).astype(int)

    df["goal_diff"] = df["home_score"] - df["away_score"]
    df["total_goals"] = df["home_score"] + df["away_score"]


    df["home_advantage"] = (~df["neutral"].astype(bool)).astype(int)

   
    latest_date = df["date"].max()
    df["days_ago"] = (latest_date - df["date"]).dt.days
    df["time_weight"] = np.exp(-df["days_ago"] / 3650)  

    modern = df[df["date"] >= "1990-01-01"].copy()

    out = OUT_DIR / "match_training_table.csv"
    modern.to_csv(out, index=False)

    print(f"Saved {out}")
    print(f"Rows: {len(modern):,}")
    print(f"Date range: {modern['date'].min().date()} to {modern['date'].max().date()}")
    print(f"Teams: {pd.unique(modern[['home_team','away_team']].values.ravel()).size}")

if __name__ == "__main__":
    main()