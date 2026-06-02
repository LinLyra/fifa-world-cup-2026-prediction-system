from pathlib import Path
import pandas as pd
import numpy as np

MATCH_FILE = Path("data/processed/match_training_fifa_only.csv")
OUT_FILE = Path("data/features/team_attack_defense_v3.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

RECENT_MATCHES = 50
SHRINK_WEIGHT = 0.70

CONF_MULT = {
    "UEFA": 1.00,
    "CONMEBOL": 0.99,
    "CAF": 0.94,
    "CONCACAF": 0.91,
    "AFC": 0.88,
    "OFC": 0.82,
}

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
    "Trinidad and Tobago": "CONCACAF", "Guatemala": "CONCACAF", "Curaçao": "CONCACAF",

    # OFC
    "New Zealand": "OFC", "Fiji": "OFC", "Tahiti": "OFC",
    "Solomon Islands": "OFC", "New Caledonia": "OFC",
}


def shrink_to_mean(value, mean=1.0, weight=SHRINK_WEIGHT):
    return weight * value + (1 - weight) * mean


def apply_confederation_adjustment(team, attack, defense):
    conf = CONFEDERATION_MAP.get(team, "UNKNOWN")
    mult = CONF_MULT.get(conf, 1.0)

    attack_adj = attack * mult

    # defense_rating 越低越好，所以这里不是直接乘
    # 而是把它相对 1.0 的优势/劣势按大洲系数缩放
    defense_adj = 1 + (defense - 1) * mult

    return conf, mult, attack_adj, defense_adj


def main():
    matches = pd.read_csv(MATCH_FILE)
    matches["date"] = pd.to_datetime(matches["date"])

    rows = []

    for _, r in matches.iterrows():
        rows.append({
            "date": r["date"],
            "team": r["home_team"],
            "opponent": r["away_team"],
            "gf": r["home_score"],
            "ga": r["away_score"],
        })

        rows.append({
            "date": r["date"],
            "team": r["away_team"],
            "opponent": r["home_team"],
            "gf": r["away_score"],
            "ga": r["home_score"],
        })

    team_matches = pd.DataFrame(rows).sort_values(["team", "date"])

    global_gf_avg = team_matches["gf"].mean()
    global_ga_avg = team_matches["ga"].mean()

    out_rows = []

    for team, tdf in team_matches.groupby("team"):
        recent = tdf.sort_values("date").tail(RECENT_MATCHES)

        raw_attack = recent["gf"].mean() / global_gf_avg
        raw_defense = recent["ga"].mean() / global_ga_avg

        attack_shrunk = shrink_to_mean(raw_attack)
        defense_shrunk = shrink_to_mean(raw_defense)

        conf, conf_mult, attack_adj, defense_adj = apply_confederation_adjustment(
            team,
            attack_shrunk,
            defense_shrunk,
        )

        attack_adj = float(np.clip(attack_adj, 0.45, 2.20))
        defense_adj = float(np.clip(defense_adj, 0.45, 2.20))

        out_rows.append({
            "team": team,
            "matches": len(tdf),
            "confederation": conf,
            "conf_multiplier": conf_mult,
            "raw_attack_rating": raw_attack,
            "raw_defense_rating": raw_defense,
            "attack_rating_shrunk": attack_shrunk,
            "defense_rating_shrunk": defense_shrunk,
            "attack_rating": attack_adj,
            "defense_rating": defense_adj,
            "net_rating": attack_adj - defense_adj,
            "last_10_goals_for": tdf.sort_values("date").tail(10)["gf"].mean(),
            "last_10_goals_against": tdf.sort_values("date").tail(10)["ga"].mean(),
        })

    out = pd.DataFrame(out_rows).sort_values("net_rating", ascending=False)
    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Teams: {len(out)}")
    print("\nTop 40 by net_rating:")
    print(
        out[
            [
                "team",
                "confederation",
                "conf_multiplier",
                "matches",
                "attack_rating",
                "defense_rating",
                "net_rating",
                "last_10_goals_for",
                "last_10_goals_against",
            ]
        ].head(40)
    )


if __name__ == "__main__":
    main()