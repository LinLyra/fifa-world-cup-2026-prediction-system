from pathlib import Path
import math
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.metrics import log_loss, brier_score_loss, accuracy_score

RAW_FILE = Path("data/raw/results.csv")
OUT_FILE = Path("data/evaluation/backtest_2022_single_matches.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

CUTOFF_DATE = "2022-11-20"
MAX_GOALS = 6
BASE_GOALS = 1.35
RHO = -0.08


def outcome_label(home_score, away_score):
    if home_score > away_score:
        return "H"
    if home_score < away_score:
        return "A"
    return "D"


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


def build_elo(matches):
    teams = sorted(set(matches["home_team"]).union(set(matches["away_team"])))
    elo = {t: 1500.0 for t in teams}

    for _, r in matches.sort_values("date").iterrows():
        h, a = r["home_team"], r["away_team"]
        hs, aw = r["home_score"], r["away_score"]

        eh = 1 / (1 + 10 ** ((elo[a] - elo[h]) / 400))

        if hs > aw:
            sh = 1
        elif hs == aw:
            sh = 0.5
        else:
            sh = 0

        k = 30 if r["tournament"] == "FIFA World Cup" else 20
        margin = abs(hs - aw)
        margin_mult = math.log(margin + 1) if margin > 0 else 1

        change = k * margin_mult * (sh - eh)

        elo[h] += change
        elo[a] -= change

    return elo


def build_attack_defense(matches):
    rows = []

    for _, r in matches.iterrows():
        rows.append({
            "team": r["home_team"],
            "gf": r["home_score"],
            "ga": r["away_score"],
            "date": r["date"],
        })
        rows.append({
            "team": r["away_team"],
            "gf": r["away_score"],
            "ga": r["home_score"],
            "date": r["date"],
        })

    df = pd.DataFrame(rows)
    global_goal_avg = df["gf"].mean()

    out = {}

    for team, tdf in df.groupby("team"):
        recent = tdf.sort_values("date").tail(50)

        attack = recent["gf"].mean() / global_goal_avg
        defense = recent["ga"].mean() / global_goal_avg

        # shrinkage，防止极端攻防评分
        attack = 0.7 * attack + 0.3 * 1.0
        defense = 0.7 * defense + 0.3 * 1.0

        out[team] = {
            "attack": float(np.clip(attack, 0.5, 2.2)),
            "defense": float(np.clip(defense, 0.5, 2.2)),
            "matches": len(tdf),
        }

    return out


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

    lh = BASE_GOALS * h_ad["attack"] * a_ad["defense"] * elo_mult_h
    la = BASE_GOALS * a_ad["attack"] * h_ad["defense"] * elo_mult_a

    lh = float(np.clip(lh, 0.25, 3.2))
    la = float(np.clip(la, 0.25, 3.2))

    matrix = score_matrix(lh, la)

    p_h = sum(p for (h, a), p in matrix.items() if h > a)
    p_d = sum(p for (h, a), p in matrix.items() if h == a)
    p_a = sum(p for (h, a), p in matrix.items() if h < a)

    best_score, best_prob = max(matrix.items(), key=lambda x: x[1])

    pred_label = max(
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
        "score_prob": best_prob,
        "pred_outcome": pred_label,
    }


def main():
    df = pd.read_csv(RAW_FILE)
    df["date"] = pd.to_datetime(df["date"])

    train = df[df["date"] < CUTOFF_DATE].copy()

    test = df[
        (df["tournament"] == "FIFA World Cup") &
        (df["date"] >= "2022-11-20") &
        (df["date"] <= "2022-12-18")
    ].copy()

    print(f"Train matches: {len(train):,}")
    print(f"2022 World Cup matches: {len(test):,}")

    elo = build_elo(train)
    ad = build_attack_defense(train)

    rows = []

    for _, r in test.iterrows():
        pred = predict_match(r["home_team"], r["away_team"], elo, ad)
        actual = outcome_label(r["home_score"], r["away_score"])

        row = r.to_dict()
        row.update(pred)
        row["actual_outcome"] = actual
        row["exact_score_hit"] = int(
            pred["pred_home_score"] == r["home_score"]
            and pred["pred_away_score"] == r["away_score"]
        )
        row["goal_error"] = abs(pred["expected_home_goals"] - r["home_score"]) + abs(
            pred["expected_away_goals"] - r["away_score"]
        )

        rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_FILE, index=False)

    y_true = out["actual_outcome"]
    y_pred = out["pred_outcome"]

    probs = out[["home_win_prob", "draw_prob", "away_win_prob"]].values
    labels = ["H", "D", "A"]

    print(f"\nSaved {OUT_FILE}")
    print("\nMetrics:")
    print(f"1X2 Accuracy: {accuracy_score(y_true, y_pred):.3f}")
    print(f"Exact Score Accuracy: {out['exact_score_hit'].mean():.3f}")
    print(f"Avg Goal Error: {out['goal_error'].mean():.3f}")
    print(f"Log Loss: {log_loss(y_true, probs, labels=labels):.3f}")

    print("\nPreview:")
    print(out[[
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "actual_outcome",
        "pred_outcome",
        "home_win_prob",
        "draw_prob",
        "away_win_prob",
        "pred_home_score",
        "pred_away_score",
        "exact_score_hit",
    ]].head(30))


if __name__ == "__main__":
    main()