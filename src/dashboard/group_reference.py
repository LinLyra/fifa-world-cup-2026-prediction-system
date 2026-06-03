"""Group A–L reference tables for Bracket / Groups tabs."""
from __future__ import annotations

import pandas as pd

from bracket_tree import LEFT_R32, R32_SLOT_LABELS, BracketMatch

GROUP_LETTERS = list("ABCDEFGHIJKL")


def _short_slot(slot: str) -> str:
    if slot.startswith("Winner Group "):
        return f"Winner {slot[-1]}"
    if slot.startswith("Runner-up Group "):
        return f"Runner-up {slot[-1]}"
    if slot.startswith("Best 3rd"):
        return "Best 3rd"
    return slot


def bracket_slot_roles(matches: list[BracketMatch]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for m in matches:
        if m.round != "Round of 32":
            continue
        slots = R32_SLOT_LABELS.get(m.match_id)
        if not slots:
            continue
        half = "Left" if m.match_id in LEFT_R32 else "Right"
        roles[m.home] = (
            f"M{m.match_id} {half} · {_short_slot(slots[0])} vs {m.away}"
        )
        roles[m.away] = (
            f"M{m.match_id} {half} · {_short_slot(slots[1])} vs {m.home}"
        )
    return roles


def group_letter_reference_table(
    fixtures_df: pd.DataFrame,
    groups_df: pd.DataFrame,
    matches: list[BracketMatch] | None = None,
) -> pd.DataFrame:
    team_group: dict[str, str] = {}
    for _, row in fixtures_df.iterrows():
        team_group[str(row["home_team"])] = str(row["group"])
        team_group[str(row["away_team"])] = str(row["group"])

    probs = groups_df.set_index("team")
    roles = bracket_slot_roles(matches) if matches else {}

    rows = []
    for letter in GROUP_LETTERS:
        teams = sorted(t for t, g in team_group.items() if g == letter)
        for team in teams:
            p = probs.loc[team] if team in probs.index else None
            rows.append(
                {
                    "Group": letter,
                    "Team": team,
                    "Win %": None if p is None else round(float(p["group_winner_prob"]) * 100, 1),
                    "Top 2 %": None if p is None else round(float(p["group_top2_prob"]) * 100, 1),
                    "Advance %": None if p is None else round(float(p["advance_prob"]) * 100, 1),
                    "This R32 draw": roles.get(team, "—"),
                }
            )
    return pd.DataFrame(rows)
