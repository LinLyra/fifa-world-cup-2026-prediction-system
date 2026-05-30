from pathlib import Path
import pandas as pd
import numpy as np

ELO_FILE = Path(
    "data/processed/current_elo_v2.csv"
)

FEATURE_FILE = Path(
    "data/features/team_features_v2.csv"
)

AD_FILE = Path(
    "data/features/team_attack_defense_v2.csv"
)

VALUE_FILE = Path(
    "data/intelligence/transfermarkt_national_team_values_v1.csv"
)

OUT_FILE = Path(
    "data/features/team_intelligence_v1.csv"
)


def normalize(series):
    return (
        (series - series.min())
        /
        (series.max() - series.min())
    )


def main():

    elo = pd.read_csv(ELO_FILE)

    feat = pd.read_csv(FEATURE_FILE)

    ad = pd.read_csv(AD_FILE)

    value = pd.read_csv(VALUE_FILE)

    df = (
        elo
        .merge(feat, on="team", how="left")
        .merge(ad, on="team", how="left")
        .merge(
            value[
                [
                    "team",
                    "market_value_eur"
                ]
            ],
            on="team",
            how="left"
        )
    )

    df["market_value_eur"] = (
        df["market_value_eur"]
        .fillna(
            df["market_value_eur"].median()
        )
    )

    df["elo_norm"] = normalize(df["elo"])

    df["market_norm"] = normalize(
        np.log1p(df["market_value_eur"])
    )

    df["attack_norm"] = normalize(
        df["attack_rating"]
    )

    df["defense_norm"] = normalize(
        1 / df["defense_rating"]
    )

    df["form_norm"] = normalize(
        df["last_10_points_per_game"]
    )

    df["intelligence_score"] = (
        0.35 * df["elo_norm"]
        + 0.25 * df["market_norm"]
        + 0.15 * df["attack_norm"]
        + 0.15 * df["defense_norm"]
        + 0.10 * df["form_norm"]
    )

    df = df.sort_values(
        "intelligence_score",
        ascending=False
    )

    df.to_csv(
        OUT_FILE,
        index=False
    )

    print(
        f"Saved {OUT_FILE}"
    )

    print(
        "\nTop 40 Teams:"
    )

    print(
        df[
            [
                "team",
                "elo",
                "market_value_eur",
                "attack_rating",
                "defense_rating",
                "intelligence_score"
            ]
        ]
        .head(40)
    )


if __name__ == "__main__":
    main()