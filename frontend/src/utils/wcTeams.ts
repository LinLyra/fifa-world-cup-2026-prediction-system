import type { ChampionRow, FixtureRow, GroupRow } from "../types";

/** World Cup 48-team universe — same logic as Streamlit wc_team_set(). */
export function wcTeamSet(
  fixtures: FixtureRow[] | null | undefined,
  groups?: GroupRow[],
  champions?: ChampionRow[]
): string[] {
  if (fixtures?.length) {
    const s = new Set<string>();
    fixtures.forEach((f) => {
      s.add(f.home_team);
      s.add(f.away_team);
    });
    return Array.from(s).sort();
  }
  if (groups?.length) {
    return Array.from(new Set(groups.map((g) => g.team))).sort();
  }
  if (champions?.length) {
    return Array.from(new Set(champions.map((c) => c.team))).sort();
  }
  return [];
}

export function isScheduledGroupFixture(
  fixtures: FixtureRow[],
  home: string,
  away: string
): boolean {
  return fixtures.some((f) => f.home_team === home && f.away_team === away);
}
