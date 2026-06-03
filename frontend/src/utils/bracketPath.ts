import type { BracketLink, BracketMatch } from "../types";

export const LEFT_R32 = [73, 74, 76, 79, 81, 82, 86, 88];
export const RIGHT_R32 = [75, 77, 78, 80, 83, 84, 85, 87];
export const LEFT_R16 = [89, 90, 91, 92];
export const RIGHT_R16 = [93, 94, 95, 96];
export const LEFT_QF = [97, 98];
export const RIGHT_QF = [99, 100];
export const LEFT_SF = [101];
export const RIGHT_SF = [102];

export const MATCH_DISPLAY_ORDER = [
  ...LEFT_R32,
  ...RIGHT_R32,
  ...LEFT_R16,
  ...RIGHT_R16,
  ...LEFT_QF,
  ...RIGHT_QF,
  ...LEFT_SF,
  ...RIGHT_SF,
  104,
];

function childMatch(feederId: number, links: BracketLink[]): number | null {
  const hit = links.find((l) => l.from_a === feederId || l.from_b === feederId);
  return hit ? hit.to : null;
}

/** Match IDs on this team's advancement chain in the consensus bracket. */
export function traceTeamPath(
  matches: BracketMatch[],
  links: BracketLink[],
  team: string | null
): Set<number> {
  if (!team) return new Set();
  const byId = Object.fromEntries(matches.map((m) => [m.match_id, m]));
  const r32Ids = new Set([...LEFT_R32, ...RIGHT_R32]);
  const start = matches.find(
    (m) => r32Ids.has(m.match_id) && (m.home === team || m.away === team)
  );
  if (!start) return new Set();

  const path = new Set<number>();
  let mid: number | null = start.match_id;
  while (mid != null && mid in byId) {
    const m = byId[mid];
    path.add(mid);
    if (m.winner !== team) break;
    mid = childMatch(mid, links);
  }
  return path;
}

export function pathChainOrdered(
  matches: BracketMatch[],
  pathIds: Set<number>
): BracketMatch[] {
  const byId = Object.fromEntries(matches.map((m) => [m.match_id, m]));
  return MATCH_DISPLAY_ORDER.filter((id) => pathIds.has(id) && id in byId).map(
    (id) => byId[id]
  );
}

export function roundShortLabel(round: string): string {
  return round.replace("Round of ", "R");
}
