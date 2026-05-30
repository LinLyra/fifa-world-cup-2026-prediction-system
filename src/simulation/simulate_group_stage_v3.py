from pathlib import Path
import pandas as pd
import numpy as np

PRED_FILE = Path("data/predictions/dixon_coles_group_predictions_v1.csv")

OUT_RANKINGS_FILE = Path("data/predictions/group_stage_rankings_v3.csv")
OUT_SUMMARY_FILE = Path("data/predictions/group_stage_simulation_v3_summary.csv")

N_SIM = 20000
MAX_GOALS = 6


def sample_score(lambda_home, lambda_away):
    return (
        min(np.random.poisson(lambda_home), MAX_GOALS),
        min(np.random.poisson(lambda_away), MAX_GOALS),
    )


def update_table(table, home, away, hg, ag):
    for team in [home, away]:
        table[team]["played"] += 1

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
    df = pd.DataFrame([
        {"team": team, **stats}
        for team, stats in table.items()
    ])

    df["tie_noise"] = np.random.random(len(df)) * 1e-6

    df = df.sort_values(
        ["points", "gd", "gf", "tie_noise"],
        ascending=[False, False, False, False]
    ).reset_index(drop=True)

    df["position"] = df.index + 1
    return df


def main():
    pred = pd.read_csv(PRED_FILE)

    all_rankings = []
    summary_counts = {}

    teams = sorted(set(pred["home_team"]).union(set(pred["away_team"])))

    for t in teams:
        summary_counts[t] = {
            "group_winner": 0,
            "group_second": 0,
            "group_top2": 0,
            "group_third": 0,
            "advance": 0,
        }

    for sim_id in range(1, N_SIM + 1):
        sim_group_rankings = []

        for group, group_matches in pred.groupby("group"):
            group_teams = sorted(
                set(group_matches["home_team"]).union(set(group_matches["away_team"]))
            )

            table = {
                team: {
                    "group": group,
                    "points": 0,
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "gf": 0,
                    "ga": 0,
                    "gd": 0,
                }
                for team in group_teams
            }

            for _, row in group_matches.iterrows():
                hg, ag = sample_score(
                    row["expected_home_goals"],
                    row["expected_away_goals"]
                )

                update_table(
                    table,
                    row["home_team"],
                    row["away_team"],
                    hg,
                    ag
                )

            ranked = rank_group(table)
            ranked["simulation_id"] = sim_id
            sim_group_rankings.append(ranked)

            for _, r in ranked.iterrows():
                team = r["team"]
                pos = int(r["position"])

                if pos == 1:
                    summary_counts[team]["group_winner"] += 1
                    summary_counts[team]["group_top2"] += 1
                    summary_counts[team]["advance"] += 1
                elif pos == 2:
                    summary_counts[team]["group_second"] += 1
                    summary_counts[team]["group_top2"] += 1
                    summary_counts[team]["advance"] += 1
                elif pos == 3:
                    summary_counts[team]["group_third"] += 1

        sim_full = pd.concat(sim_group_rankings, ignore_index=True)

        thirds = sim_full[sim_full["position"] == 3].copy()
        thirds["third_tie_noise"] = np.random.random(len(thirds)) * 1e-6

        best_thirds = thirds.sort_values(
            ["points", "gd", "gf", "third_tie_noise"],
            ascending=[False, False, False, False]
        ).head(8)

        sim_full["advanced"] = False

        # Top 2 advance
        sim_full.loc[sim_full["position"].isin([1, 2]), "advanced"] = True

        # Best 8 third-place advance
        best_third_keys = set(
            zip(best_thirds["group"], best_thirds["team"])
        )

        sim_full["is_best_third"] = sim_full.apply(
            lambda r: (r["group"], r["team"]) in best_third_keys,
            axis=1
        )

        sim_full.loc[sim_full["is_best_third"], "advanced"] = True

        for team in best_thirds["team"]:
            summary_counts[team]["advance"] += 1

        all_rankings.append(sim_full)

    rankings_out = pd.concat(all_rankings, ignore_index=True)

    # Save full rankings for bracket simulation
    rankings_out.to_csv(OUT_RANKINGS_FILE, index=False)

    summary_rows = []
    for team, c in summary_counts.items():
        summary_rows.append({
            "team": team,
            "group_winner_prob": c["group_winner"] / N_SIM,
            "group_second_prob": c["group_second"] / N_SIM,
            "group_top2_prob": c["group_top2"] / N_SIM,
            "group_third_prob": c["group_third"] / N_SIM,
            "advance_prob": c["advance"] / N_SIM,
        })

    summary = pd.DataFrame(summary_rows).sort_values(
        "advance_prob",
        ascending=False
    )

    summary.to_csv(OUT_SUMMARY_FILE, index=False)

    print(f"Saved {OUT_RANKINGS_FILE}")
    print(f"Saved {OUT_SUMMARY_FILE}")
    print(f"Simulations: {N_SIM}")

    print("\nRankings preview:")
    print(rankings_out.head(24))

    print("\nTop 40 summary:")
    print(summary.head(40))


if __name__ == "__main__":
    main()