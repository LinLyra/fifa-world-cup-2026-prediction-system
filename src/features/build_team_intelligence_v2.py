from pathlib import Path
import pandas as pd
import numpy as np

INTEL_V1_FILE = Path("data/features/team_intelligence_v1.csv")
ODDS_FILE = Path("data/intelligence/worldcup_winner_odds_seed.csv")
OUT_FILE = Path("data/features/team_intelligence_v2.csv")


def normalize(series):
    s = series.astype(float)
    if s.max() == s.min():
        return s * 0
    return (s - s.min()) / (s.max() - s.min())


def fractional_to_decimal(frac):
    if pd.isna(frac):
        return np.nan

    frac = str(frac).strip()

    if "/" not in frac:
        return np.nan

    a, b = frac.split("/")
    return float(a) / float(b) + 1.0


def main():
    intel = pd.read_csv(INTEL_V1_FILE)
    odds = pd.read_csv(ODDS_FILE)

    odds["decimal_odds"] = odds["odds_fractional"].apply(fractional_to_decimal)
    odds["implied_prob_raw"] = 1 / odds["decimal_odds"]

  
    odds["market_champion_prob"] = (
        odds["implied_prob_raw"] / odds["implied_prob_raw"].sum()
    )

    df = intel.merge(
        odds[["team", "decimal_odds", "market_champion_prob", "source"]],
        on="team",
        how="left"
    )

    # 没有赔率的队伍给极低市场概率
    min_prob = odds["market_champion_prob"].min() * 0.35
    df["market_champion_prob"] = df["market_champion_prob"].fillna(min_prob)
    df["decimal_odds"] = df["decimal_odds"].fillna(999.0)
    df["source"] = df["source"].fillna("not_listed")

    df["market_score"] = normalize(np.log1p(df["market_champion_prob"]))

  
    df["intelligence_score_v2"] = (
        0.30 * df["elo_norm"]
        + 0.25 * df["market_norm"]
        + 0.25 * df["market_score"]
        + 0.10 * df["attack_norm"]
        + 0.07 * df["defense_norm"]
        + 0.03 * df["form_norm"]
    )

    df = df.sort_values("intelligence_score_v2", ascending=False)

    df.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print("\nTop 40 Teams:")
    print(
        df[
            [
                "team",
                "elo",
                "market_value_eur",
                "decimal_odds",
                "market_champion_prob",
                "intelligence_score_v2",
            ]
        ].head(40)
    )


if __name__ == "__main__":
    main()