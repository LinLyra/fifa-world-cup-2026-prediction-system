export const COLORS = {
  pitch: "#1B5E20",
  pitchLight: "#2E7D32",
  gold: "#C9A227",
  bg: "#F7F9F8",
  draw: "#78909C",
  away: "#1565C0",
};

export const SIMULATIONS = 20_000;
export const CHAMPION_MIN_PROB = 0.002;
export const CHAMPION_TOP_N = 15;
export const PATH_TABLE_TOP_N = 15;

export function pct(x: number, digits = 1): string {
  return `${(x * 100).toFixed(digits)}%`;
}

export function formatMarketValue(eur: number | null | undefined): string {
  if (eur == null || Number.isNaN(eur)) return "—";
  if (eur >= 1_000_000_000) return `€${(eur / 1_000_000_000).toFixed(2)}B`;
  if (eur >= 1_000_000) return `€${Math.round(eur / 1_000_000)}M`;
  return `€${eur.toLocaleString()}`;
}

export function parseScorelines(raw: string): [string, number][] {
  if (!raw?.trim()) return [];
  const out: [string, number][] = [];
  for (const part of raw.split(";")) {
    const trimmed = part.trim();
    const match = trimmed.match(/^([^:]+):([\d.]+)$/);
    if (match) out.push([match[1].trim(), parseFloat(match[2])]);
  }
  return out;
}

export function pathDifficultyLabel(percentile: number | null | undefined): [string, string] {
  if (percentile == null || Number.isNaN(percentile)) return ["—", "—"];
  const p = percentile;
  if (p >= 0.75) return ["★★★★★", "Hard"];
  if (p >= 0.55) return ["★★★★☆", "Hard"];
  if (p >= 0.35) return ["★★★☆☆", "Medium"];
  if (p >= 0.15) return ["★★☆☆☆", "Easy"];
  return ["★☆☆☆☆", "Easy"];
}

export function championProbForTeam(
  team: string,
  pathRow: { champion_prob?: number },
  champions: { team: string; champion_prob: number }[]
): number | undefined {
  if (pathRow.champion_prob != null && !Number.isNaN(pathRow.champion_prob)) {
    return pathRow.champion_prob;
  }
  return champions.find((c) => c.team === team)?.champion_prob;
}
