from pathlib import Path
import math
import pandas as pd
import numpy as np
from scipy.stats import poisson

FIXTURES_FILE = Path("data/raw/group_fixtures_final.csv")
ATTACK_DEFENSE_FILE = Path("data/features/team_attack_defense_v2.csv")
ELO_FILE = Path("data/processed/current_elo_v2.csv")

OUT_DIR = Path("data/predictions")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "dixon_coles_group_predictions_v1.csv"

MAX_GOALS = 6
BASE_GOALS = 1.35
RHO = -0.08  # Dixon-Coles low-score correlation adjustment


def load_strength_tables():
    ad = pd.read_csv(ATTACK_DEFENSE_FILE)
    elo = pd.read_csv(ELO_FILE)

    df = ad.merge(
        elo.rename(columns={"elo": "custom_elo"}),
        on="team",
        how="left"
    )

    df["custom_elo"] = df["custom_elo"].fillna(1500)


    df["sample_weight"] = np.minimum(df["matches"] / 150, 1.0)

    df["attack_rating_adj"] = (
        df["sample_weight"] * df["attack_rating"]
        + (1 - df["sample_weight"]) * 1.0
    )

    df["defense_rating_adj"] = (
        df["sample_weight"] * df["defense_rating"]
        + (1 - df["sample_weight"]) * 1.0
    )

    return df.set_index("team").to_dict("index")


def expected_goals(team_a, team_b, strengths):
    a = strengths.get(team_a, {})
    b = strengths.get(team_b, {})

    a_attack = a.get("attack_rating_adj", 1.0)
    b_defense = b.get("defense_rating_adj", 1.0)

    b_attack = b.get("attack_rating_adj", 1.0)
    a_defense = a.get("defense_rating_adj", 1.0)

    a_elo = a.get("custom_elo", 1500)
    b_elo = b.get("custom_elo", 1500)

    elo_diff = a_elo - b_elo

    elo_multiplier_a = math.exp(elo_diff / 1600)
    elo_multiplier_b = math.exp(-elo_diff / 1600)

    lambda_a = BASE_GOALS * a_attack * b_defense * elo_multiplier_a
    lambda_b = BASE_GOALS * b_attack * a_defense * elo_multiplier_b

    lambda_a = float(np.clip(lambda_a, 0.25, 3.20))
    lambda_b = float(np.clip(lambda_b, 0.25, 3.20))

    return lambda_a, lambda_b


def dixon_coles_tau(home_goals, away_goals, lambda_home, lambda_away, rho=RHO):
    """
    Dixon-Coles correction for low-score football outcomes.
    Applies only to 0-0, 0-1, 1-0, 1-1.
    """
    if home_goals == 0 and away_goals == 0:
        return 1 - (lambda_home * lambda_away * rho)

    if home_goals == 0 and away_goals == 1:
        return 1 + (lambda_home * rho)

    if home_goals == 1 and away_goals == 0:
        return 1 + (lambda_away * rho)

    if home_goals == 1 and away_goals == 1:
        return 1 - rho

    return 1.0


def score_matrix(lambda_home, lambda_away, max_goals=MAX_GOALS):
    matrix = {}

    for hg in range(max_goals + 1):
        for ag in range(max_goals + 1):
            base_p = poisson.pmf(hg, lambda_home) * poisson.pmf(ag, lambda_away)
            tau = dixon_coles_tau(hg, ag, lambda_home, lambda_away)
            matrix[(hg, ag)] = max(base_p * tau, 0)

    total = sum(matrix.values())
    matrix = {k: v / total for k, v in matrix.items()}

    return matrix


def summarize_probs(matrix):
    home_win = sum(p for (h, a), p in matrix.items() if h > a)
    draw = sum(p for (h, a), p in matrix.items() if h == a)
    away_win = sum(p for (h, a), p in matrix.items() if h < a)

    best_score, best_prob = max(matrix.items(), key=lambda x: x[1])

    return {
        "pred_home_score": best_score[0],
        "pred_away_score": best_score[1],
        "score_probability": best_prob,
        "home_win_prob": home_win,
        "draw_prob": draw,
        "away_win_prob": away_win,
    }


def main():
    fixtures = pd.read_csv(FIXTURES_FILE)
    strengths = load_strength_tables()

    rows = []

    for _, r in fixtures.iterrows():
        home = r["home_team"]
        away = r["away_team"]

        lambda_home, lambda_away = expected_goals(home, away, strengths)
        matrix = score_matrix(lambda_home, lambda_away)
        summary = summarize_probs(matrix)

        row = r.to_dict()
        row.update({
            "expected_home_goals": lambda_home,
            "expected_away_goals": lambda_away,
        })
        row.update(summary)

        top_scores = sorted(matrix.items(), key=lambda x: x[1], reverse=True)[:8]
        row["top_8_scorelines"] = "; ".join(
            [f"{h}-{a}:{p:.3f}" for (h, a), p in top_scores]
        )

        rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Rows: {len(out)}")
    print("\nPreview:")
    print(out[[
        "home_team",
        "away_team",
        "expected_home_goals",
        "expected_away_goals",
        "pred_home_score",
        "pred_away_score",
        "home_win_prob",
        "draw_prob",
        "away_win_prob",
        "top_8_scorelines",
    ]].head(25))


if __name__ == "__main__":
    main()