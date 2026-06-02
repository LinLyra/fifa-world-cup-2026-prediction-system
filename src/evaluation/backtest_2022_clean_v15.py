from pathlib import Path
import math
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.metrics import accuracy_score, log_loss

RAW_FILE = Path("data/raw/results.csv")
OUT_FILE = Path("data/evaluation/backtest_2022_clean_v15.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

CUTOFF_DATE = "2022-11-20"
MAX_GOALS = 6
BASE_GOALS = 1.35
RHO = -0.08
SHRINK_WEIGHT = 0.70
MARKET_PROXY_WEIGHT = 0.25


def outcome_label(h, a):
    if h > a:
        return "H"
    if h < a:
        return "A"
    return "D"


def build_elo(matches):
    teams = sorted(set(matches["home_team"]) | set(matches["away_team"]))
    elo = {t: 1500.0 for t in teams}

    for _, r in matches.sort_values("date").iterrows():
        h, a = r["home_team"], r["away_team"]
        hs, aw = r["home_score"], r["away_score"]

        expected_h = 1 / (1 + 10 ** ((elo[a] - elo[h]) / 400))
        actual_h = 1 if hs > aw else 0.5 if hs == aw else 0

        k = 30 if r["tournament"] == "FIFA World Cup" else 20
        margin = abs(hs - aw)
        margin_mult = math.log(margin + 1) if margin > 0 else 1

        change = k * margin_mult * (actual_h - expected_h)
        elo[h] += change
        elo[a] -= change

    return elo


def build_attack_defense(matches):
    rows = []

    for _, r in matches.iterrows():
        rows.append({
            "date": r["date"],
            "team": r["home_team"],
            "gf": r["home_score"],
            "ga": r["away_score"],
        })
        rows.append({
            "date": r["date"],
            "team": r["away_team"],
            "gf": r["away_score"],
            "ga": r["home_score"],
        })

    df = pd.DataFrame(rows)

    global_gf = df["gf"].mean()
    global_ga = df["ga"].mean()

    ratings = {}

    for team, tdf in df.groupby("team"):
        recent = tdf.sort_values("date").tail(50)

        raw_attack = recent["gf"].mean() / global_gf
        raw_defense = recent["ga"].mean() / global_ga

        attack = SHRINK_WEIGHT * raw_attack + (1 - SHRINK_WEIGHT) * 1.0
        defense = SHRINK_WEIGHT * raw_defense + (1 - SHRINK_WEIGHT) * 1.0

        ratings[team] = {
            "attack": float(np.clip(attack, 0.50, 2.20)),
            "defense": float(np.clip(defense, 0.50, 2.20)),
        }

    return ratings


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


def predict_match(home, away, elo, ad):
    h_elo = elo.get(home, 1500)
    a_elo = elo.get(away, 1500)

    h_ad = ad.get(home, {"attack": 1.0, "defense": 1.0})
    a_ad = ad.get(away, {"attack": 1.0, "defense": 1.0})

    elo_diff = h_elo - a_elo

    elo_mult_h = math.exp(elo_diff / 2000)
    elo_mult_a = math.exp(-elo_diff / 2000)

    # If there is no 2022 real odds, use Elo proxy to simulate market prior, avoid data leakage
    market_mult_h = math.exp(MARKET_PROXY_WEIGHT * elo_diff / 1200)
    market_mult_a = math.exp(-MARKET_PROXY_WEIGHT * elo_diff / 1200)

    lh = BASE_GOALS * h_ad["attack"] * a_ad["defense"] * elo_mult_h * market_mult_h
    la = BASE_GOALS * a_ad["attack"] * h_ad["defense"] * elo_mult_a * market_mult_a

    lh = float(np.clip(lh, 0.25, 3.20))
    la = float(np.clip(la, 0.25, 3.20))

    matrix = score_matrix(lh, la)

    p_h = sum(p for (h, a), p in matrix.items() if h > a)
    p_d = sum(p for (h, a), p in matrix.items() if h == a)
    p_a = sum(p for (h, a), p in matrix.items() if h < a)

    best_score, best_prob = max(matrix.items(), key=lambda x: x[1])

    pred_outcome = max(
        {"H": p_h, "D": p_d, "A": p_a},
        key={"H": p_h, "D": p_d, "A": p_a}.get
    )

    return {
        "expected_home_goals": lh,
        "expected_away_goals": la,
        "home_win_prob": p_h,
        "draw_prob": p_d,
        "away_win_prob": p_a,
        "pred_home_score": best_score[0],
        "pred_away_score": best_score[1],
        "score_probability": best_prob,
        "pred_outcome": pred_outcome,
    }


def main():
    df = pd.read_csv(RAW_FILE)
    df["date"] = pd.to_datetime(df["date"])

    train = df[df["date"] < CUTOFF_DATE].copy()

    test = df[
        (df["tournament"] == "FIFA World Cup")
        & (df["date"] >= "2022-11-20")
        & (df["date"] <= "2022-12-18")
    ].copy()

    elo = build_elo(train)
    ad = build_attack_defense(train)

    rows = []

    for _, r in test.iterrows():
        pred = predict_match(r["home_team"], r["away_team"], elo, ad)
        actual = outcome_label(r["home_score"], r["away_score"])

        row = {
            "date": r["date"],
            "home_team": r["home_team"],
            "away_team": r["away_team"],
            "home_score": r["home_score"],
            "away_score": r["away_score"],
            "actual_outcome": actual,
            **pred,
        }

        row["exact_score_hit"] = int(
            row["pred_home_score"] == r["home_score"]
            and row["pred_away_score"] == r["away_score"]
        )

        row["goal_error"] = abs(row["expected_home_goals"] - r["home_score"]) + abs(
            row["expected_away_goals"] - r["away_score"]
        )

        rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_FILE, index=False)

    y_true = out["actual_outcome"]
    y_pred = out["pred_outcome"]
    probs = out[["home_win_prob", "draw_prob", "away_win_prob"]].values

    print(f"Saved {OUT_FILE}")
    print(f"Train matches: {len(train):,}")
    print(f"2022 World Cup matches: {len(test):,}")
    print()
    print("Metrics:")
    print("1X2 Accuracy:", round(accuracy_score(y_true, y_pred), 4))
    print("Exact Score Accuracy:", round(out["exact_score_hit"].mean(), 4))
    print("Avg Goal Error:", round(out["goal_error"].mean(), 4))
    print("Log Loss:", round(log_loss(y_true, probs, labels=["H", "D", "A"]), 4))
    print()
    print(out[[
        "date", "home_team", "away_team",
        "home_score", "away_score",
        "home_win_prob", "draw_prob", "away_win_prob",
        "pred_home_score", "pred_away_score",
        "exact_score_hit"
    ]].head(30))


if __name__ == "__main__":
    main()