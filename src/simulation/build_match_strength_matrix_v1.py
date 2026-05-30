from pathlib import Path
import math
import pandas as pd
import numpy as np
from scipy.stats import poisson

TEAM_FILE = Path("data/features/team_intelligence_v2.csv")
OUT_FILE = Path("data/predictions/match_strength_matrix_v1.csv")

MAX_GOALS = 6
BASE_GOALS = 1.35
RHO = -0.08


def dixon_coles_tau(h, a, lh, la, rho=RHO):
    if h == 0 and a == 0:
        return 1 - lh * la * rho
    if h == 0 and a == 1:
        return 1 + lh * rho
    if h == 1 and a == 0:
        return 1 + la * rho
    if h == 1 and a == 1:
        return 1 - rho
    return 1.0


def score_matrix(lh, la):
    matrix = {}

    for h in range(MAX_GOALS + 1):
        for a in range(MAX_GOALS + 1):
            p = poisson.pmf(h, lh) * poisson.pmf(a, la)
            p *= dixon_coles_tau(h, a, lh, la)
            matrix[(h, a)] = max(p, 0)

    total = sum(matrix.values())
    return {k: v / total for k, v in matrix.items()}


def summarize(matrix):
    home_win = sum(p for (h, a), p in matrix.items() if h > a)
    draw = sum(p for (h, a), p in matrix.items() if h == a)
    away_win = sum(p for (h, a), p in matrix.items() if h < a)

    best, best_p = max(matrix.items(), key=lambda x: x[1])

    return {
        "home_win_prob": home_win,
        "draw_prob": draw,
        "away_win_prob": away_win,
        "pred_home_score": best[0],
        "pred_away_score": best[1],
        "score_probability": best_p,
    }


def expected_goals(team_a, team_b, teams):
    a = teams.loc[team_a]
    b = teams.loc[team_b]

    a_attack = a["attack_rating"]
    b_defense = b["defense_rating"]

    b_attack = b["attack_rating"]
    a_defense = a["defense_rating"]

    elo_diff = a["elo"] - b["elo"]
    intel_diff = a["intelligence_score_v2"] - b["intelligence_score_v2"]

    elo_mult_a = math.exp(elo_diff / 1800)
    elo_mult_b = math.exp(-elo_diff / 1800)

    intel_mult_a = math.exp(intel_diff / 1.8)
    intel_mult_b = math.exp(-intel_diff / 1.8)

    lh = BASE_GOALS * a_attack * b_defense * elo_mult_a * intel_mult_a
    la = BASE_GOALS * b_attack * a_defense * elo_mult_b * intel_mult_b

    lh = float(np.clip(lh, 0.25, 3.50))
    la = float(np.clip(la, 0.25, 3.50))

    return lh, la


def main():
    teams = pd.read_csv(TEAM_FILE)

    required = [
        "team",
        "elo",
        "attack_rating",
        "defense_rating",
        "intelligence_score_v2",
    ]

    teams = teams.dropna(subset=required)
    teams = teams.set_index("team")

    rows = []

    team_list = list(teams.index)

    for home in team_list:
        for away in team_list:
            if home == away:
                continue

            lh, la = expected_goals(home, away, teams)
            matrix = score_matrix(lh, la)
            summary = summarize(matrix)

            row = {
                "home_team": home,
                "away_team": away,
                "expected_home_goals": lh,
                "expected_away_goals": la,
            }
            row.update(summary)

            top_scores = sorted(matrix.items(), key=lambda x: x[1], reverse=True)[:5]
            row["top_5_scorelines"] = "; ".join(
                [f"{h}-{a}:{p:.3f}" for (h, a), p in top_scores]
            )

            rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Rows: {len(out):,}")
    print("\nPreview:")
    print(out.head(20))


if __name__ == "__main__":
    main()