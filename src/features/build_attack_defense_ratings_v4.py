from pathlib import Path
import pandas as pd
import numpy as np

MATCH_FILE = Path("data/processed/match_training_fifa_only.csv")
ELO_FILE = Path("data/features/current_elo_v2.csv")
OUT_FILE = Path("data/features/team_attack_defense_v4.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

RECENT_MATCHES = 50
SHRINK_WEIGHT = 0.65

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
    "Russia": "UEFA", "Czech Republic": "UEFA", "Slovakia": "UEFA", "Slovenia": "UEFA",
    "Hungary": "UEFA", "Romania": "UEFA", "Greece": "UEFA", "Ireland": "UEFA",

    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Colombia": "CONMEBOL", "Chile": "CONMEBOL", "Ecuador": "CONMEBOL",
    "Paraguay": "CONMEBOL", "Peru": "CONMEBOL", "Bolivia": "CONMEBOL",
    "Venezuela": "CONMEBOL",

    "Morocco": "CAF", "Senegal": "CAF", "Algeria": "CAF", "Tunisia": "CAF",
    "Egypt": "CAF", "Nigeria": "CAF", "Ghana": "CAF", "Cameroon": "CAF",
    "Ivory Coast": "CAF", "South Africa": "CAF", "Mali": "CAF",

    "Japan": "AFC", "South Korea": "AFC", "Iran": "AFC", "Australia": "AFC",
    "Saudi Arabia": "AFC", "Qatar": "AFC", "Iraq": "AFC", "Uzbekistan": "AFC",
    "China": "AFC", "Jordan": "AFC", "Thailand": "AFC", "Vietnam": "AFC",

    "United States": "CONCACAF", "Mexico": "CONCACAF", "Canada": "CONCACAF",
    "Costa Rica": "CONCACAF", "Panama": "CONCACAF", "Jamaica": "CONCACAF",
    "Honduras": "CONCACAF", "Haiti": "CONCACAF", "Curaçao": "CONCACAF",

    "New Zealand": "OFC", "Fiji": "OFC", "Tahiti": "OFC",
}


def opponent_attack_weight(opponent_elo):
    # conservative handling: opponent strength weight limited to 0.80 ~ 1.15
    return float(np.clip(opponent_elo / 1800, 0.80, 1.15))


def opponent_defense_weight(opponent_elo):
    # more valuable for strong teams to lose fewer goals; more penalty for weak teams to lose goals
    return float(np.clip(opponent_elo / 1800, 0.80, 1.15))


def shrink(value, weight=SHRINK_WEIGHT):
    return weight * value + (1 - weight) * 1.0


def apply_confederation(team, attack, defense):
    conf = CONFEDERATION_MAP.get(team, "UNKNOWN")
    mult = CONF_MULT.get(conf, 1.0)

    attack_adj = attack * mult
    defense_adj = 1 + (defense - 1) * mult

    return conf, mult, attack_adj, defense_adj


def main():
    matches = pd.read_csv(MATCH_FILE)
    matches["date"] = pd.to_datetime(matches["date"])

    elo_df = pd.read_csv(ELO_FILE)
    elo_map = dict(zip(elo_df["team"], elo_df["elo"]))

    rows = []

    for _, r in matches.iterrows():
        home_opp_elo = elo_map.get(r["away_team"], 1500)
        away_opp_elo = elo_map.get(r["home_team"], 1500)

        rows.append({
            "date": r["date"],
            "team": r["home_team"],
            "opponent": r["away_team"],
            "gf": r["home_score"],
            "ga": r["away_score"],
            "opp_elo": home_opp_elo,
            "weighted_gf": r["home_score"] * opponent_attack_weight(home_opp_elo),
            "weighted_ga": r["away_score"] * opponent_defense_weight(home_opp_elo),
        })

        rows.append({
            "date": r["date"],
            "team": r["away_team"],
            "opponent": r["home_team"],
            "gf": r["away_score"],
            "ga": r["home_score"],
            "opp_elo": away_opp_elo,
            "weighted_gf": r["away_score"] * opponent_attack_weight(away_opp_elo),
            "weighted_ga": r["home_score"] * opponent_defense_weight(away_opp_elo),
        })

    df = pd.DataFrame(rows).sort_values(["team", "date"])

    global_gf = df["weighted_gf"].mean()
    global_ga = df["weighted_ga"].mean()

    out_rows = []

    for team, tdf in df.groupby("team"):
        recent = tdf.sort_values("date").tail(RECENT_MATCHES)

        raw_attack = recent["weighted_gf"].mean() / global_gf
        raw_defense = recent["weighted_ga"].mean() / global_ga

        attack_shrunk = shrink(raw_attack)
        defense_shrunk = shrink(raw_defense)

        conf, conf_mult, attack_adj, defense_adj = apply_confederation(
            team,
            attack_shrunk,
            defense_shrunk,
        )

        attack_adj = float(np.clip(attack_adj, 0.50, 2.05))
        defense_adj = float(np.clip(defense_adj, 0.50, 2.05))

        out_rows.append({
            "team": team,
            "matches": len(tdf),
            "confederation": conf,
            "conf_multiplier": conf_mult,
            "avg_opponent_elo_recent50": recent["opp_elo"].mean(),
            "raw_attack_rating": raw_attack,
            "raw_defense_rating": raw_defense,
            "attack_rating": attack_adj,
            "defense_rating": defense_adj,
            "net_rating": attack_adj - defense_adj,
            "last_10_goals_for": tdf.tail(10)["gf"].mean(),
            "last_10_goals_against": tdf.tail(10)["ga"].mean(),
        })

    out = pd.DataFrame(out_rows).sort_values("net_rating", ascending=False)
    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Teams: {len(out)}")
    print("\nTop 40 by net_rating:")
    print(out[[
        "team",
        "confederation",
        "conf_multiplier",
        "avg_opponent_elo_recent50",
        "attack_rating",
        "defense_rating",
        "net_rating",
        "last_10_goals_for",
        "last_10_goals_against",
    ]].head(40))


if __name__ == "__main__":
    main()