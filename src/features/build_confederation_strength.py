from pathlib import Path
import math
import pandas as pd
import numpy as np

RAW_FILE = Path("data/raw/results.csv")
OUT_FILE = Path("data/features/confederation_strength.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

START_DATE = "1990-01-01"

CONFEDERATION_MAP = {
    # UEFA
    "France": "UEFA", "England": "UEFA", "Germany": "UEFA", "Spain": "UEFA",
    "Portugal": "UEFA", "Netherlands": "UEFA", "Belgium": "UEFA", "Italy": "UEFA",
    "Croatia": "UEFA", "Denmark": "UEFA", "Switzerland": "UEFA", "Austria": "UEFA",
    "Serbia": "UEFA", "Poland": "UEFA", "Norway": "UEFA", "Sweden": "UEFA",
    "Scotland": "UEFA", "Wales": "UEFA", "Ukraine": "UEFA", "Turkey": "UEFA",
    "Russia": "UEFA", "Czech Republic": "UEFA", "Slovakia": "UEFA", "Slovenia": "UEFA",
    "Hungary": "UEFA", "Romania": "UEFA", "Greece": "UEFA", "Ireland": "UEFA",
    "Northern Ireland": "UEFA", "Finland": "UEFA", "Iceland": "UEFA",

    # CONMEBOL
    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Colombia": "CONMEBOL", "Chile": "CONMEBOL", "Ecuador": "CONMEBOL",
    "Paraguay": "CONMEBOL", "Peru": "CONMEBOL", "Bolivia": "CONMEBOL",
    "Venezuela": "CONMEBOL",

    # CAF
    "Morocco": "CAF", "Senegal": "CAF", "Algeria": "CAF", "Tunisia": "CAF",
    "Egypt": "CAF", "Nigeria": "CAF", "Ghana": "CAF", "Cameroon": "CAF",
    "Ivory Coast": "CAF", "South Africa": "CAF", "Mali": "CAF", "Burkina Faso": "CAF",
    "DR Congo": "CAF", "Cape Verde": "CAF", "Angola": "CAF",

    # AFC
    "Japan": "AFC", "South Korea": "AFC", "Iran": "AFC", "Australia": "AFC",
    "Saudi Arabia": "AFC", "Qatar": "AFC", "Iraq": "AFC", "United Arab Emirates": "AFC",
    "Uzbekistan": "AFC", "China": "AFC", "Jordan": "AFC", "Syria": "AFC",
    "Oman": "AFC", "Bahrain": "AFC", "Thailand": "AFC", "Vietnam": "AFC",

    # CONCACAF
    "United States": "CONCACAF", "Mexico": "CONCACAF", "Canada": "CONCACAF",
    "Costa Rica": "CONCACAF", "Panama": "CONCACAF", "Jamaica": "CONCACAF",
    "Honduras": "CONCACAF", "El Salvador": "CONCACAF", "Haiti": "CONCACAF",
    "Trinidad and Tobago": "CONCACAF", "Guatemala": "CONCACAF",

    # OFC
    "New Zealand": "OFC", "Fiji": "OFC", "Tahiti": "OFC",
    "Solomon Islands": "OFC", "New Caledonia": "OFC",
}


def match_result_score(gf, ga):
    if gf > ga:
        return 1.0
    if gf == ga:
        return 0.5
    return 0.0


def build_elo(matches):
    teams = sorted(set(matches["home_team"]).union(set(matches["away_team"])))
    elo = {t: 1500.0 for t in teams}

    for _, r in matches.sort_values("date").iterrows():
        h = r["home_team"]
        a = r["away_team"]
        hs = r["home_score"]
        aw = r["away_score"]

        eh = 1 / (1 + 10 ** ((elo[a] - elo[h]) / 400))
        sh = match_result_score(hs, aw)

        k = 30 if r["tournament"] == "FIFA World Cup" else 20
        margin = abs(hs - aw)
        margin_mult = math.log(margin + 1) if margin > 0 else 1

        change = k * margin_mult * (sh - eh)

        elo[h] += change
        elo[a] -= change

    return elo


def main():
    df = pd.read_csv(RAW_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= START_DATE].copy()

    df["home_conf"] = df["home_team"].map(CONFEDERATION_MAP)
    df["away_conf"] = df["away_team"].map(CONFEDERATION_MAP)

    df = df.dropna(subset=["home_conf", "away_conf"])

    # 只用跨洲比赛学习大洲强度
    inter = df[df["home_conf"] != df["away_conf"]].copy()

    elo = build_elo(df)

    rows = []

    for _, r in inter.iterrows():
        h = r["home_team"]
        a = r["away_team"]

        h_conf = r["home_conf"]
        a_conf = r["away_conf"]

        h_elo = elo.get(h, 1500)
        a_elo = elo.get(a, 1500)

        expected_h = 1 / (1 + 10 ** ((a_elo - h_elo) / 400))
        actual_h = match_result_score(r["home_score"], r["away_score"])

        residual_h = actual_h - expected_h
        residual_a = -residual_h

        rows.append({
            "confederation": h_conf,
            "opponent_confederation": a_conf,
            "team": h,
            "opponent": a,
            "residual": residual_h,
            "goals_for": r["home_score"],
            "goals_against": r["away_score"],
        })

        rows.append({
            "confederation": a_conf,
            "opponent_confederation": h_conf,
            "team": a,
            "opponent": h,
            "residual": residual_a,
            "goals_for": r["away_score"],
            "goals_against": r["home_score"],
        })

    residuals = pd.DataFrame(rows)

    conf = residuals.groupby("confederation").agg(
        matches=("residual", "count"),
        avg_residual=("residual", "mean"),
        gf_pg=("goals_for", "mean"),
        ga_pg=("goals_against", "mean"),
    ).reset_index()

    # 把 residual 映射成 0.82 - 1.04 区间的大洲实力系数
    conf["raw_multiplier"] = 1 + conf["avg_residual"] * 0.8

    # 以 UEFA / CONMEBOL 为锚点
    anchor = conf[conf["confederation"].isin(["UEFA", "CONMEBOL"])]["raw_multiplier"].mean()
    conf["conf_multiplier"] = conf["raw_multiplier"] / anchor

    conf["conf_multiplier"] = conf["conf_multiplier"].clip(0.82, 1.04)

    conf = conf.sort_values("conf_multiplier", ascending=False)

    conf.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Inter-confederation matches used: {len(inter):,}")
    print()
    print(conf)


if __name__ == "__main__":
    main()