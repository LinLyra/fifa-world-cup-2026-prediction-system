import type { BracketMatch, FixtureRow, GroupRow } from "../types";

/** FIFA R32 slot labels (match_id → home/away slot text). */
export const R32_SLOT_LABELS: Record<number, { home: string; away: string }> = {
  73: { home: "Runner-up Group A", away: "Runner-up Group B" },
  74: { home: "Winner Group C", away: "Runner-up Group F" },
  75: { home: "Winner Group E", away: "Best 3rd (Groups A/B/C/D/F)" },
  76: { home: "Winner Group F", away: "Runner-up Group C" },
  77: { home: "Runner-up Group E", away: "Runner-up Group I" },
  78: { home: "Winner Group I", away: "Best 3rd (Groups C/D/F/G/H)" },
  79: { home: "Winner Group A", away: "Best 3rd (Groups C/E/F/H/I)" },
  80: { home: "Winner Group L", away: "Best 3rd (Groups E/H/I/J/K)" },
  81: { home: "Winner Group G", away: "Best 3rd (Groups A/E/H/I/J)" },
  82: { home: "Winner Group D", away: "Best 3rd (Groups B/E/F/I/J)" },
  83: { home: "Runner-up Group K", away: "Runner-up Group L" },
  84: { home: "Winner Group H", away: "Runner-up Group J" },
  85: { home: "Winner Group B", away: "Best 3rd (Groups E/F/G/I/J)" },
  86: { home: "Runner-up Group D", away: "Runner-up Group G" },
  87: { home: "Winner Group J", away: "Runner-up Group H" },
  88: { home: "Winner Group K", away: "Best 3rd (Groups D/E/I/J/L)" },
};

const LEFT_R32 = new Set([73, 74, 76, 79, 81, 82, 86, 88]);

export type BracketSlotRole = {
  matchId: number;
  side: "home" | "away";
  slotLabel: string;
  half: "Left" | "Right";
  opponent: string;
};

export type GroupTeamRow = {
  team: string;
  groupWinnerProb: number;
  top2Prob: number;
  advanceProb: number;
  bracketRole: string | null;
};

export type GroupLetterBlock = {
  letter: string;
  teams: GroupTeamRow[];
};

export const GROUP_LETTERS = "ABCDEFGHIJKL".split("");

export function teamsByGroup(fixtures: FixtureRow[]): Record<string, string[]> {
  const map: Record<string, Set<string>> = {};
  for (const f of fixtures) {
    if (!f.group) continue;
    map[f.group] ??= new Set();
    map[f.group].add(f.home_team);
    map[f.group].add(f.away_team);
  }
  const out: Record<string, string[]> = {};
  for (const letter of GROUP_LETTERS) {
    out[letter] = [...(map[letter] ?? [])].sort();
  }
  return out;
}

function shortSlotLabel(slot: string): string {
  const w = slot.match(/Winner Group ([A-L])/);
  if (w) return `Winner ${w[1]}`;
  const r = slot.match(/Runner-up Group ([A-L])/);
  if (r) return `Runner-up ${r[1]}`;
  if (slot.startsWith("Best 3rd")) return "Best 3rd";
  return slot;
}

/** Map each team in the modal R32 draw to slot + opponent. */
export function bracketRolesFromR32(matches: BracketMatch[]): Map<string, BracketSlotRole> {
  const roles = new Map<string, BracketSlotRole>();
  for (const m of matches) {
    if (m.round !== "Round of 32") continue;
    const slots = R32_SLOT_LABELS[m.match_id];
    if (!slots) continue;
    const half = LEFT_R32.has(m.match_id) ? "Left" : "Right";
    roles.set(m.home, {
      matchId: m.match_id,
      side: "home",
      slotLabel: slots.home,
      half,
      opponent: m.away,
    });
    roles.set(m.away, {
      matchId: m.match_id,
      side: "away",
      slotLabel: slots.away,
      half,
      opponent: m.home,
    });
  }
  return roles;
}

export function formatBracketRole(role: BracketSlotRole): string {
  return `M${role.matchId} ${role.half} · ${shortSlotLabel(role.slotLabel)} vs ${role.opponent}`;
}

export function buildGroupLetterBlocks(
  fixtures: FixtureRow[],
  groups: GroupRow[],
  r32Matches: BracketMatch[]
): GroupLetterBlock[] {
  const byGroup = teamsByGroup(fixtures);
  const probByTeam = new Map(groups.map((g) => [g.team, g]));
  const roles = bracketRolesFromR32(r32Matches);

  return GROUP_LETTERS.map((letter) => ({
    letter,
    teams: (byGroup[letter] ?? []).map((team) => {
      const p = probByTeam.get(team);
      const role = roles.get(team);
      return {
        team,
        groupWinnerProb: p?.group_winner_prob ?? 0,
        top2Prob: p?.group_top2_prob ?? 0,
        advanceProb: p?.advance_prob ?? 0,
        bracketRole: role ? formatBracketRole(role) : null,
      };
    }),
  }));
}
