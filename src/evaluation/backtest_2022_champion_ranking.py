from pathlib import Path
import math
import pandas as pd
import numpy as np
from scipy.stats import poisson

RAW_FILE = Path("data/raw/results.csv")
OUT_FILE = Path("data/evaluation/backtest_2022_champion_ranking.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

CUTOFF_DATE = "2022-11-20"
MAX_GOALS = 6
BASE_GOALS = 1.35
RHO = -0.08
N_SIM = 20000

GROUPS_2022 = {
    "A": ["Qatar", "Ecuador", "Senegal", "Netherlands"],
    "B": ["England", "Iran", "United States", "Wales"],
    "C": ["Argentina", "Saudi Arabia", "Mexico", "Poland"],
    "D": ["France", "Australia", "Denmark", "Tunisia"],
    "E": ["Spain", "Costa Rica", "Germany", "Japan"],
    "F": ["Belgium", "Canada", "Morocco", "Croatia"],
    "G": ["Brazil", "Serbia", "Switzerland", "Cameroon"],
    "H": ["Portugal", "Ghana", "Uruguay", "South Korea"],
}

R16_SLOTS_2022 = [
    ("A1", "B2"),
    ("C1", "D2"),
    ("B1", "A2"),
    ("D1", "C2"),
    ("E1", "F2"),
    ("G1", "H2"),
    ("F1", "E2"),
    ("H1", "G2"),
]


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


def outcome_points(hg, ag):
    if hg > ag:
        return 3, 0
    if hg < ag:
        return 0, 3
    return 1, 1


def build_elo(matches):
    teams = sorted(set(matches["home_team"]).union(set(matches["away_team"])))
    elo = {t: 1500.0 for t in teams}

    for _, r in matches.sort_values("date").iterrows():
        h, a = r["home_team"], r["away_team"]
        hs, aw = r["home_score"], r["away_score"]

        eh = 1 / (1 + 10 ** ((elo[a] - elo[h]) / 400))
        sh = 1 if hs > aw else 0.5 if hs == aw else 0

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

        attack = 0.7 * attack + 0.3 * 1.0
        defense = 0.7 * defense + 0.3 * 1.0

        out[team] = {
            "attack": float(np.clip(attack, 0.5, 2.2)),
            "defense": float(np.clip(defense, 0.5, 2.2)),
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


def expected_goals(team_a, team_b, elo, ad):
    a_elo = elo.get(team_a, 1500)
    b_elo = elo.get(team_b, 1500)

    a_ad = ad.get(team_a, {"attack": 1.0, "defense": 1.0})
    b_ad = ad.get(team_b, {"attack": 1.0, "defense": 1.0})

    elo_diff = a_elo - b_elo

    elo_mult_a = math.exp(elo_diff / 2000)
    elo_mult_b = math.exp(-elo_diff / 2000)

    la = BASE_GOALS * a_ad["attack"] * b_ad["defense"] * elo_mult_a
    lb = BASE_GOALS * b_ad["attack"] * a_ad["defense"] * elo_mult_b

    la = float(np.clip(la, 0.25, 3.2))
    lb = float(np.clip(lb, 0.25, 3.2))

    return la, lb


def sample_score(team_a, team_b, elo, ad):
    la, lb = expected_goals(team_a, team_b, elo, ad)

    ga = min(np.random.poisson(la), MAX_GOALS)
    gb = min(np.random.poisson(lb), MAX_GOALS)

    return ga, gb


def knockout_winner(team_a, team_b, elo, ad):
    la, lb = expected_goals(team_a, team_b, elo, ad)
    matrix = score_matrix(la, lb)

    p_a = sum(p for (a, b), p in matrix.items() if a > b)
    p_d = sum(p for (a, b), p in matrix.items() if a == b)
    p_b = sum(p for (a, b), p in matrix.items() if a < b)

    p_a = p_a + 0.5 * p_d
    p_b = p_b + 0.5 * p_d

    total = p_a + p_b
    p_a /= total
    p_b /= total

    return np.random.choice([team_a, team_b], p=[p_a, p_b])


def simulate_group(group_teams, elo, ad):
    table = {
        team: {
            "points": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
        }
        for team in group_teams
    }

    for i in range(len(group_teams)):
        for j in range(i + 1, len(group_teams)):
            a = group_teams[i]
            b = group_teams[j]

            ga, gb = sample_score(a, b, elo, ad)
            pa, pb = outcome_points(ga, gb)

            table[a]["points"] += pa
            table[b]["points"] += pb

            table[a]["gf"] += ga
            table[a]["ga"] += gb
            table[b]["gf"] += gb
            table[b]["ga"] += ga

            table[a]["gd"] = table[a]["gf"] - table[a]["ga"]
            table[b]["gd"] = table[b]["gf"] - table[b]["ga"]

    rows = []
    for team, s in table.items():
        rows.append({"team": team, **s})

    df = pd.DataFrame(rows)
    df["tie_noise"] = np.random.random(len(df)) * 1e-6

    df = df.sort_values(
        ["points", "gd", "gf", "tie_noise"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

    df["position"] = df.index + 1
    return df


def main():
    df = pd.read_csv(RAW_FILE)
    df["date"] = pd.to_datetime(df["date"])

    train = df[df["date"] < CUTOFF_DATE].copy()

    elo = build_elo(train)
    ad = build_attack_defense(train)

    teams = sorted([t for group in GROUPS_2022.values() for t in group])

    counts = {
        t: {
            "r16": 0,
            "qf": 0,
            "sf": 0,
            "final": 0,
            "champion": 0,
        }
        for t in teams
    }

    for _ in range(N_SIM):
        group_results = {}

        for group, group_teams in GROUPS_2022.items():
            ranked = simulate_group(group_teams, elo, ad)
            group_results[f"{group}1"] = ranked.iloc[0]["team"]
            group_results[f"{group}2"] = ranked.iloc[1]["team"]

            counts[ranked.iloc[0]["team"]]["r16"] += 1
            counts[ranked.iloc[1]["team"]]["r16"] += 1

        r16_winners = []
        for slot_a, slot_b in R16_SLOTS_2022:
            team_a = group_results[slot_a]
            team_b = group_results[slot_b]
            winner = knockout_winner(team_a, team_b, elo, ad)
            r16_winners.append(winner)
            counts[winner]["qf"] += 1

        qf_pairs = [
            (r16_winners[0], r16_winners[1]),
            (r16_winners[2], r16_winners[3]),
            (r16_winners[4], r16_winners[5]),
            (r16_winners[6], r16_winners[7]),
        ]

        qf_winners = []
        for a, b in qf_pairs:
            winner = knockout_winner(a, b, elo, ad)
            qf_winners.append(winner)
            counts[winner]["sf"] += 1

        sf_pairs = [
            (qf_winners[0], qf_winners[1]),
            (qf_winners[2], qf_winners[3]),
        ]

        sf_winners = []
        for a, b in sf_pairs:
            winner = knockout_winner(a, b, elo, ad)
            sf_winners.append(winner)
            counts[winner]["final"] += 1

        champion = knockout_winner(sf_winners[0], sf_winners[1], elo, ad)
        counts[champion]["champion"] += 1

    rows = []
    for team, c in counts.items():
        rows.append({
            "team": team,
            "r16_prob": c["r16"] / N_SIM,
            "qf_prob": c["qf"] / N_SIM,
            "sf_prob": c["sf"] / N_SIM,
            "final_prob": c["final"] / N_SIM,
            "champion_prob": c["champion"] / N_SIM,
            "elo_pre_2022": elo.get(team, 1500),
            "attack_pre_2022": ad.get(team, {}).get("attack", 1.0),
            "defense_pre_2022": ad.get(team, {}).get("defense", 1.0),
        })

    out = pd.DataFrame(rows).sort_values("champion_prob", ascending=False)
    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Simulations: {N_SIM}")
    print("\nTop 32 champion probabilities:")
    print(out.head(32))

    print("\nActual key teams:")
    key = ["Argentina", "France", "Croatia", "Morocco"]
    print(out[out["team"].isin(key)])


if __name__ == "__main__":
    main()