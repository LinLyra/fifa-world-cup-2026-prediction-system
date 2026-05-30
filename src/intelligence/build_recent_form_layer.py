from pathlib import Path
import pandas as pd
import numpy as np

MATCH_FILE = Path("data/processed/match_training_fifa_only.csv")
OUT_FILE = Path("data/intelligence/recent_form_layer_v1.csv")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def points(gf, ga):
    if gf > ga:
        return 3
    if gf == ga:
        return 1
    return 0


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
            "points": points(r["home_score"], r["away_score"]),
            "tournament": r["tournament"],
        })
        rows.append({
            "date": r["date"],
            "team": r["away_team"],
            "opponent": r["home_team"],
            "gf": r["away_score"],
            "ga": r["home_score"],
            "points": points(r["away_score"], r["home_score"]),
            "tournament": r["tournament"],
        })

    df = pd.DataFrame(rows).sort_values(["team", "date"])

    out_rows = []

    for team, tdf in df.groupby("team"):
        tdf = tdf.sort_values("date")

        row = {"team": team, "last_match_date": tdf["date"].max()}

        for n in [5, 10, 20]:
            recent = tdf.tail(n)

            row[f"form_{n}_matches"] = len(recent)
            row[f"form_{n}_ppg"] = recent["points"].mean()
            row[f"form_{n}_gf_pg"] = recent["gf"].mean()
            row[f"form_{n}_ga_pg"] = recent["ga"].mean()
            row[f"form_{n}_gd_pg"] = (recent["gf"] - recent["ga"]).mean()
            row[f"form_{n}_win_rate"] = (recent["points"] == 3).mean()
            row[f"form_{n}_clean_sheet_rate"] = (recent["ga"] == 0).mean()

        out_rows.append(row)

    out = pd.DataFrame(out_rows)

    out["recent_form_score"] = (
        0.45 * out["form_10_ppg"].fillna(1.0) / 3
        + 0.25 * out["form_20_ppg"].fillna(1.0) / 3
        + 0.20 * ((out["form_10_gd_pg"].fillna(0) + 3) / 6)
        + 0.10 * out["form_10_clean_sheet_rate"].fillna(0.2)
    )

    out["recent_form_score"] = out["recent_form_score"].clip(0, 1)

    out = out.sort_values("recent_form_score", ascending=False)
    out.to_csv(OUT_FILE, index=False)

    print(f"Saved {OUT_FILE}")
    print(out[[
        "team",
        "last_match_date",
        "form_10_ppg",
        "form_10_gf_pg",
        "form_10_ga_pg",
        "form_10_gd_pg",
        "recent_form_score"
    ]].head(40))


if __name__ == "__main__":
    main()