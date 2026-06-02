from pathlib import Path
import sys
import pandas as pd
import numpy as np

INTEL_FILE = Path("data/features/team_intelligence_v2.csv")
ELO_FILE = Path("data/raw/official_elo/eloratings.csv")
ATTACK_FILE = Path("data/features/team_attack_defense_v2.csv")
FIXTURE_FILE = Path("data/raw/group_fixtures_final.csv")

BACKUP_FILE = Path("data/features/team_intelligence_v2.backup.csv")
OUT_FILE = INTEL_FILE

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.team_name_utils import canonical_team_name

TEAM_ALIAS_TO_SOURCE = {
    "USA": "United States",
    "Côte d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde",
    "South Korea": "South Korea",
    "Saudi Arabia": "Saudi Arabia",
    "New Zealand": "New Zealand",
    "South Africa": "South Africa",
}

PLAYOFF_DEFAULTS = {
    "UEFA Playoff A": {"elo": 1650, "market_value_eur": 120_000_000, "attack_rating": 1.03, "defense_rating": 0.98},
    "UEFA Playoff B": {"elo": 1650, "market_value_eur": 120_000_000, "attack_rating": 1.03, "defense_rating": 0.98},
    "UEFA Playoff C": {"elo": 1650, "market_value_eur": 120_000_000, "attack_rating": 1.03, "defense_rating": 0.98},
    "UEFA Playoff D": {"elo": 1650, "market_value_eur": 120_000_000, "attack_rating": 1.03, "defense_rating": 0.98},
    "FIFA Playoff 1": {"elo": 1580, "market_value_eur": 60_000_000, "attack_rating": 0.98, "defense_rating": 1.02},
    "FIFA Playoff 2": {"elo": 1580, "market_value_eur": 60_000_000, "attack_rating": 0.98, "defense_rating": 1.02},
}


def find_row(df, team):
    if "team" not in df.columns:
        return None
    hit = df[df["team"] == team]
    if len(hit) > 0:
        return hit.iloc[0]
    return None


def normalize_score(series):
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def load_official_elo_latest(path: Path) -> pd.DataFrame:
    """
    Convert official Elo history table to a 2-column team/elo snapshot.
    `eloratings.csv` columns: date, team, rating, change
    """
    df = pd.read_csv(path)

    df["team"] = df["team"].astype(str).apply(canonical_team_name)
    df["date_parsed"] = pd.to_datetime(df.get("date"), errors="coerce")

    if df["date_parsed"].notna().any():
        df = df.sort_values("date_parsed")

    latest = df.groupby("team", as_index=False).tail(1)

    out = latest[["team", "rating"]].rename(columns={"rating": "elo"})
    out["elo"] = pd.to_numeric(out["elo"], errors="coerce")
    out = out.dropna(subset=["team", "elo"])
    return out


def main():
    intel = pd.read_csv(INTEL_FILE)
    elo = load_official_elo_latest(ELO_FILE)
    atk = pd.read_csv(ATTACK_FILE)
    fixtures = pd.read_csv(FIXTURE_FILE)

    # Canonicalize team names across all inputs
    intel["team"] = intel["team"].apply(canonical_team_name)
    elo["team"] = elo["team"].apply(canonical_team_name)
    atk["team"] = atk["team"].apply(canonical_team_name)
    fixtures["home_team"] = fixtures["home_team"].apply(canonical_team_name)
    fixtures["away_team"] = fixtures["away_team"].apply(canonical_team_name)

    # De-dupe intelligence after canonicalization (prefer later rows if any)
    intel = intel.drop_duplicates(subset=["team"], keep="last")

    if not BACKUP_FILE.exists():
        intel.to_csv(BACKUP_FILE, index=False)
        print(f"Backup saved: {BACKUP_FILE}")

    wc_teams = sorted(
        set(fixtures["home_team"].dropna()) |
        set(fixtures["away_team"].dropna())
    )

    # Build quick lookups from official Elo and attack/defense tables
    elo_map = dict(zip(elo["team"], elo["elo"]))
    atk_map = atk.set_index("team")[["attack_rating", "defense_rating"]].to_dict("index") if "team" in atk.columns else {}

    # For ALL World Cup teams already present, refresh Elo and A/D if available.
    # This prevents previously "patched-in" default rows (elo=1500, attack=1, defense=1)
    # from sticking around after name canonicalization.
    wc_mask = intel["team"].isin(wc_teams)
    intel.loc[wc_mask, "elo"] = intel.loc[wc_mask, "team"].map(elo_map).fillna(intel.loc[wc_mask, "elo"])
    if "attack_rating" in intel.columns and "defense_rating" in intel.columns and atk_map:
        intel.loc[wc_mask, "attack_rating"] = intel.loc[wc_mask, "team"].map(lambda t: atk_map.get(t, {}).get("attack_rating")).fillna(
            intel.loc[wc_mask, "attack_rating"]
        )
        intel.loc[wc_mask, "defense_rating"] = intel.loc[wc_mask, "team"].map(lambda t: atk_map.get(t, {}).get("defense_rating")).fillna(
            intel.loc[wc_mask, "defense_rating"]
        )

    new_rows = []

    for team in wc_teams:
        if team in set(intel["team"]):
            continue

        if team in PLAYOFF_DEFAULTS:
            base = PLAYOFF_DEFAULTS[team]
            new_rows.append({
                "team": team,
                "elo": base["elo"],
                "market_value_eur": base["market_value_eur"],
                "decimal_odds": 999.0,
                "market_champion_prob": 1 / 999,
                "attack_rating": base["attack_rating"],
                "defense_rating": base["defense_rating"],
            })
            continue

        source_name = canonical_team_name(team)

        elo_row = find_row(elo, source_name)
        atk_row = find_row(atk, source_name)
        intel_row = find_row(intel, source_name)

        new_rows.append({
            "team": team,
            "elo": float(elo_row["elo"]) if elo_row is not None and "elo" in elo_row else (
                float(intel_row["elo"]) if intel_row is not None and "elo" in intel_row else 1500.0
            ),
            "market_value_eur": float(intel_row["market_value_eur"]) if intel_row is not None and "market_value_eur" in intel_row else 80_000_000,
            "decimal_odds": float(intel_row["decimal_odds"]) if intel_row is not None and "decimal_odds" in intel_row else 999.0,
            "market_champion_prob": float(intel_row["market_champion_prob"]) if intel_row is not None and "market_champion_prob" in intel_row else 1 / 999,
            "attack_rating": float(atk_row["attack_rating"]) if atk_row is not None and "attack_rating" in atk_row else (
                float(intel_row["attack_rating"]) if intel_row is not None and "attack_rating" in intel_row else 1.0
            ),
            "defense_rating": float(atk_row["defense_rating"]) if atk_row is not None and "defense_rating" in atk_row else (
                float(intel_row["defense_rating"]) if intel_row is not None and "defense_rating" in intel_row else 1.0
            ),
        })

    if new_rows:
        add = pd.DataFrame(new_rows)

        for col in intel.columns:
            if col not in add.columns:
                add[col] = np.nan

        add = add[intel.columns]
        intel = pd.concat([intel, add], ignore_index=True)

    # 重新计算 intelligence_score_v2，避免新增队伍分数为空
    elo_norm = normalize_score(intel["elo"])
    value_norm = normalize_score(np.log1p(pd.to_numeric(intel["market_value_eur"], errors="coerce").fillna(0)))
    market_norm = normalize_score(pd.to_numeric(intel["market_champion_prob"], errors="coerce").fillna(0))

    if "attack_rating" in intel.columns and "defense_rating" in intel.columns:
        attack_norm = normalize_score(intel["attack_rating"])
        defense_norm = 1 - normalize_score(intel["defense_rating"])
        strength_norm = 0.5 * attack_norm + 0.5 * defense_norm
    else:
        strength_norm = pd.Series([0.5] * len(intel))

    intel["intelligence_score_v2"] = (
        0.35 * elo_norm +
        0.25 * value_norm +
        0.25 * market_norm +
        0.15 * strength_norm
    )

    intel = intel.drop_duplicates(subset=["team"], keep="last")
    intel.to_csv(OUT_FILE, index=False)

    final_teams = set(intel["team"])
    missing = [t for t in wc_teams if t not in final_teams]

    print(f"Saved repaired {OUT_FILE}")
    print(f"World Cup teams: {len(wc_teams)}")
    print(f"Missing after repair: {len(missing)}")
    print(missing)

    print("\nAdded rows:")
    print(pd.DataFrame(new_rows)[["team", "elo", "market_value_eur", "attack_rating", "defense_rating"]] if new_rows else "None")


if __name__ == "__main__":
    main()