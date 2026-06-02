from pathlib import Path
import math
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.metrics import accuracy_score, log_loss

RAW_FILE = Path("data/raw/results.csv")
OUT_FILE = Path("data/evaluation/backtest_2022_engine_versions.csv")
SUMMARY_FILE = Path("data/evaluation/backtest_2022_engine_versions_summary.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

CUTOFF_DATE = "2022-11-20"
MAX_GOALS = 6
BASE_GOALS = 1.35
RHO = -0.08

MARKET_XG_WEIGHT = 0.35
SHRINK_WEIGHT_V15 = 0.70
SHRINK_WEIGHT_V16 = 0.70

CONF_MULT = {
    "UEFA": 1.00,
    "CONMEBOL": 0.99,
    "CAF": 0.94,
    "CONCACAF": 0.91,
    "AFC": 0.88,
    "OFC": 0.82,
}

CONFEDERATION_MAP = {
    "France": "UEFA", "England": "UEFA", "Germany": "UEFA", "Spain": "UEFA",
    "Portugal": "UEFA", "Netherlands": "UEFA", "Belgium": "UEFA", "Italy": "UEFA",
    "Croatia": "UEFA", "Denmark": "UEFA", "Switzerland": "UEFA", "Austria": "UEFA",
    "Serbia": "UEFA", "Poland": "UEFA", "Norway": "UEFA", "Sweden": "UEFA",
    "Scotland": "UEFA", "Wales": "UEFA", "Ukraine": "UEFA", "Turkey": "UEFA",

    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Colombia": "CONMEBOL", "Chile": "CONMEBOL", "Ecuador": "CONMEBOL",
    "Paraguay": "CONMEBOL", "Peru": "CONMEBOL",

    "Morocco": "CAF", "Senegal": "CAF", "Algeria": "CAF", "Tunisia": "CAF",
    "Egypt": "CAF", "Nigeria": "CAF", "Ghana": "CAF", "Cameroon": "CAF",
    "Ivory Coast": "CAF", "South Africa": "CAF", "Mali": "CAF",

    "Japan": "AFC", "South Korea": "AFC", "Iran": "AFC", "Australia": "AFC",
    "Saudi Arabia": "AFC", "Qatar": "AFC", "Iraq": "AFC", "Uzbekistan": "AFC",

    "United States": "CONCACAF", "Mexico": "CONCACAF", "Canada": "CONCACAF",
    "Costa Rica": "CONCACAF", "Panama": "CONCACAF", "Jamaica": "CONCACAF",

    "New Zealand": "OFC",
}


def outcome_label(h, a):
    if h > a:
        return "H"
    if h < a:
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

        expected_h = 1 / (1 + 10 ** ((elo[a] - elo[h]) / 400))
        actual_h = 1 if hs > aw else 0.5 if hs == aw else 0

        k = 30 if r["tournament"] == "FIFA World Cup" else 20
        margin = abs(hs - aw)
        margin_mult = math.log(margin + 1) if margin > 0 else 1

        change = k * margin_mult * (actual_h - expected_h)
        elo[h] += change
        elo[a] -= change

    return elo


def build_attack_defense(matches, version):
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

    out = {}

    for team, tdf in df.groupby("team"):
        recent = tdf.sort_values("date").tail(50)

        raw_attack = recent["gf"].mean() / global_gf
        raw_defense = recent["ga"].mean() / global_ga

        attack = SHRINK_WEIGHT_V15 * raw_attack + (1 - SHRINK_WEIGHT_V15) * 1.0
        defense = SHRINK_WEIGHT_V15 * raw_defense + (1 - SHRINK_WEIGHT_V15) * 1.0

        conf = CONFEDERATION_MAP.get(team, "UNKNOWN")
        conf_mult = CONF_MULT.get(conf, 1.0)

        if version == "v16_conf_market":
            attack = attack * conf_mult
            defense = 1 + (defense - 1) * conf_mult

        out[team] = {
            "attack": float(np.clip(attack, 0.50, 2.20)),
            "defense": float(np.clip(defense, 0.50, 2.20)),
            "confederation": conf,
            "conf_multiplier": conf_mult,
        }

    return out


def build_market_prior(elo, teams):
    """
    Important Note:
    Here we do not use 2026 odds to avoid data leakage.
    If you have 2022 pre-tournament odds in the future, you can replace here.
    Currently using pre-2022 Elo to generate market proxy, only used for testing "market calibration structure".
    """
    values = {}
    for t in teams:
        e = elo.get(t, 1500)
        values[t] = math.exp((e - 1500) / 280)

    total = sum(values.values())
    return {t: values[t] / total for t in values}


def score_matrix(lh, la):
    matrix = {}

    for h in range(MAX_GOALS + 1):
        for a in range(MAX_GOALS + 1):
            p = poisson.pmf(h, lh) * poisson.pmf(a, la)
            p *= dixon_coles_tau(h, a, lh, la)
            matrix[(h, a)] = max(p, 0)

    total = sum(matrix.values())
    return {k: v / total for k, v in matrix.items()}


def predict_match(home, away, elo, ad, market_prior):
    h_elo = elo.get(home, 1500)
    a_elo = elo.get(away, 1500)

    h_ad = ad.get(home, {"attack": 1.0, "defense": 1.0})
    a_ad = ad.get(away, {"attack": 1.0, "defense": 1.0})

    elo_diff = h_elo - a_elo

    elo_mult_h = math.exp(elo_diff / 2000)
    elo_mult_a = math.exp(-elo_diff / 2000)

    h_market = max(market_prior.get(home, 1e-6), 1e-6)
    a_market = max(market_prior.get(away, 1e-6), 1e-6)
    market_diff = math.log(h_market) - math.log(a_market)

    market_mult_h = math.exp(MARKET_XG_WEIGHT * market_diff / 3.0)
    market_mult_a = math.exp(-MARKET_XG_WEIGHT * market_diff / 3.0)

    lh = BASE_GOALS * h_ad["attack"] * a_ad["defense"] * elo_mult_h * market_mult_h
    la = BASE_GOALS * a_ad["attack"] * h_ad["defense"] * elo_mult_a * market_mult_a

    lh = float(np.clip(lh, 0.25, 3.20))
    la = float(np.clip(la, 0.25, 3.20))

    matrix = score_matrix(lh, la)

    p_h = sum(p for (h, a), p in matrix.items() if h > a)
    p_d = sum(p for (h, a), p in matrix.items() if h == a)
    p_a = sum(p for (h, a), p in matrix.items() if h < a)

    best_score, best_prob = max(matrix.items(), key=lambda x: x[1])

    pred = max({"H": p_h, "D": p_d, "A": p_a}, key={"H": p_h, "D": p_d, "A": p_a}.get)

    return {
        "expected_home_goals": lh,
        "expected_away_goals": la,
        "home_win_prob": p_h,
        "draw_prob": p_d,
        "away_win_prob": p_a,
        "pred_home_score": best_score[0],
        "pred_away_score": best_score[1],
        "score_prob": best_prob,
        "pred_outcome": pred,
    }


def evaluate_version(version, train, test):
    elo = build_elo(train)
    ad = build_attack_defense(train, version)

    teams = sorted(set(test["home_team"]).union(set(test["away_team"])))
    market_prior = build_market_prior(elo, teams)

    rows = []

    for _, r in test.iterrows():
        pred = predict_match(r["home_team"], r["away_team"], elo, ad, market_prior)
        actual = outcome_label(r["home_score"], r["away_score"])

        row = {
            "version": version,
            "date": r["date"],
            "home_team": r["home_team"],
            "away_team": r["away_team"],
            "home_score": r["home_score"],
            "away_score": r["away_score"],
            "actual_outcome": actual,
            **pred,
        }

        row["exact_score_hit"] = int(
            pred["pred_home_score"] == r["home_score"]
            and pred["pred_away_score"] == r["away_score"]
        )

        row["goal_error"] = abs(pred["expected_home_goals"] - r["home_score"]) + abs(
            pred["expected_away_goals"] - r["away_score"]
        )

        rows.append(row)

    out = pd.DataFrame(rows)

    y_true = out["actual_outcome"]
    y_pred = out["pred_outcome"]
    probs = out[["home_win_prob", "draw_prob", "away_win_prob"]].values

    summary = {
        "version": version,
        "matches": len(out),
        "accuracy_1x2": accuracy_score(y_true, y_pred),
        "exact_score_accuracy": out["exact_score_hit"].mean(),
        "avg_goal_error": out["goal_error"].mean(),
        "log_loss": log_loss(y_true, probs, labels=["H", "D", "A"]),
    }

    return out, summary


def main():
    df = pd.read_csv(RAW_FILE)
    df["date"] = pd.to_datetime(df["date"])

    train = df[df["date"] < CUTOFF_DATE].copy()

    test = df[
        (df["tournament"] == "FIFA World Cup")
        & (df["date"] >= "2022-11-20")
        & (df["date"] <= "2022-12-18")
    ].copy()

    print(f"Train matches: {len(train):,}")
    print(f"2022 World Cup matches: {len(test):,}")

    versions = [
        "v15_market",
        "v16_conf_market",
    ]

    all_rows = []
    summaries = []

    for v in versions:
        result, summary = evaluate_version(v, train, test)
        all_rows.append(result)
        summaries.append(summary)

    all_out = pd.concat(all_rows, ignore_index=True)
    summary_out = pd.DataFrame(summaries)

    all_out.to_csv(OUT_FILE, index=False)
    summary_out.to_csv(SUMMARY_FILE, index=False)

    print(f"\nSaved {OUT_FILE}")
    print(f"Saved {SUMMARY_FILE}")

    print("\nVersion Comparison:")
    print(summary_out)

    print("\nPreview:")
    print(all_out[[
        "version",
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
    ]].head(40))


if __name__ == "__main__":
    main()