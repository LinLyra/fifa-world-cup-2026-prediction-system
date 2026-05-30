from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import poisson

PRED_FILE = Path("data/predictions/dixon_coles_group_predictions_v1.csv")
OUT_FILE = Path("data/predictions/group_stage_simulation_v2.csv")

N_SIM = 20000
MAX_GOALS = 6


def sample_score(lambda_home, lambda_away):
    home_goals = min(np.random.poisson(lambda_home), MAX_GOALS)
    away_goals = min(np.random.poisson(lambda_away), MAX_GOALS)
    return home_goals, away_goals


def update_table(table, home, away, hg, ag):
    table[home]["played"] += 1
    table[away]["played"] += 1

    table[home]["gf"] += hg
    table[home]["ga"] += ag
    table[away]["gf"] += ag
    table[away]["ga"] += hg

    table[home]["gd"] = table[home]["gf"] - table[home]["ga"]
    table[away]["gd"] = table[away]["gf"] - table[away]["ga"]

    if hg > ag:
        table[home]["points"] += 3
        table[home]["wins"] += 1
        table[away]["losses"] += 1
    elif hg < ag:
        table[away]["points"] += 3
        table[away]["wins"] += 1
        table[home]["losses"] += 1
    else:
        table[home]["points"] += 1
        table[away]["points"] += 1
        table[home]["draws"] += 1
        table[away]["draws"] += 1


def rank_group(table):
    rows = []

    for team, stats in table.items():
        rows.append({
            "team": team,
            **stats
        })

    df = pd.DataFrame(rows)

    # FIFA-style simplified ranking:
    # points → goal difference → goals for → random tiebreak noise
    df["tie_noise"] = np.random.random(len(df)) * 1e-6

    df = df.sort_values(
        ["points", "gd", "gf", "tie_noise"],
        ascending=[False, False, False, False]
    ).reset_index(drop=True)

    df["rank"] = df.index + 1
    return df


def main():
    pred = pd.read_csv(PRED_FILE)

    all_teams = sorted(set(pred["home_team"]).union(set(pred["away_team"])))

    counts = {
        team: {
            "group_winner": 0,
            "group_second": 0,
            "group_top2": 0,
            "group_third": 0,
            "advance": 0,
            "avg_points": 0.0,
            "avg_gd": 0.0,
            "avg_gf": 0.0,
        }
        for team in all_teams
    }

    for _ in range(N_SIM):
        all_group_rankings = []

        for group, group_matches in pred.groupby("group"):
            teams = sorted(
                set(group_matches["home_team"]).union(set(group_matches["away_team"]))
            )

            table = {
                team: {
                    "points": 0,
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "gf": 0,
                    "ga": 0,
                    "gd": 0,
                    "group": group,
                }
                for team in teams
            }

            for _, row in group_matches.iterrows():
                home = row["home_team"]
                away = row["away_team"]

                hg, ag = sample_score(
                    row["expected_home_goals"],
                    row["expected_away_goals"]
                )

                update_table(table, home, away, hg, ag)

            ranked = rank_group(table)
            ranked["group"] = group
            all_group_rankings.append(ranked)

            for _, r in ranked.iterrows():
                team = r["team"]

                counts[team]["avg_points"] += r["points"]
                counts[team]["avg_gd"] += r["gd"]
                counts[team]["avg_gf"] += r["gf"]

                if r["rank"] == 1:
                    counts[team]["group_winner"] += 1
                    counts[team]["group_top2"] += 1
                    counts[team]["advance"] += 1

                elif r["rank"] == 2:
                    counts[team]["group_second"] += 1
                    counts[team]["group_top2"] += 1
                    counts[team]["advance"] += 1

                elif r["rank"] == 3:
                    counts[team]["group_third"] += 1

        full_rankings = pd.concat(all_group_rankings, ignore_index=True)

        # 8 best third-place teams advance
        thirds = full_rankings[full_rankings["rank"] == 3].copy()
        thirds["tie_noise"] = np.random.random(len(thirds)) * 1e-6

        best_thirds = thirds.sort_values(
            ["points", "gd", "gf", "tie_noise"],
            ascending=[False, False, False, False]
        ).head(8)

        for team in best_thirds["team"]:
            counts[team]["advance"] += 1

    rows = []

    for team, c in counts.items():
        rows.append({
            "team": team,
            "group_winner_prob": c["group_winner"] / N_SIM,
            "group_second_prob": c["group_second"] / N_SIM,
            "group_top2_prob": c["group_top2"] / N_SIM,
            "group_third_prob": c["group_third"] / N_SIM,
            "advance_prob": c["advance"] / N_SIM,
            "avg_points": c["avg_points"] / N_SIM,
            "avg_gd": c["avg_gd"] / N_SIM,
            "avg_gf": c["avg_gf"] / N_SIM,
        })

    out = pd.DataFrame(rows)
    out = out.sort_values("advance_prob", ascending=False)

    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(f"Simulations: {N_SIM}")
    print("\nTop 40 advance probabilities:")
    print(out.head(40))


if __name__ == "__main__":
    main()