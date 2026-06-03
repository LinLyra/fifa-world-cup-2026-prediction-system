import type { FinalIntelRow, IntelligenceRow, MatchMatrixRow } from "../types";

export function modelConfidence(
  teamA: string,
  teamB: string,
  row: MatchMatrixRow,
  intel: IntelligenceRow[] | null,
  fin: FinalIntelRow | null
): { level: "High" | "Medium" | "Low"; reasons: string[] } {
  const reasons: string[] = [];
  let score = 0;

  const hw = row.home_win_prob;
  const dr = row.draw_prob;
  const aw = row.away_win_prob;
  const sorted = [hw, dr, aw].sort((a, b) => b - a);
  const favouriteMargin = sorted[0] - sorted[1];

  const ia = intel?.find((t) => t.team === teamA);
  const ib = intel?.find((t) => t.team === teamB);

  if (ia && ib) {
    const eloGap = Math.abs(ia.elo - ib.elo);
    if (eloGap >= 120) {
      reasons.push("Large Elo gap between teams");
      score += 2;
    } else if (eloGap >= 60) {
      reasons.push("Moderate strength separation");
      score += 1;
    } else {
      reasons.push("Teams closely matched on Elo");
    }

    const modelFav = hw >= aw ? teamA : teamB;
    const marketFav = ia.market_champion_prob >= ib.market_champion_prob ? teamA : teamB;
    if (modelFav === marketFav) {
      reasons.push("Market sentiment aligns with model favourite");
      score += 1;
    }
  }

  if (favouriteMargin >= 0.22) {
    reasons.push("Clear favourite in win probabilities");
    score += 1;
  } else if (favouriteMargin >= 0.12) {
    reasons.push("Moderate edge in win probabilities");
  } else {
    reasons.push("Toss-up — outcome probabilities are tight");
    score -= 1;
  }

  if (fin) {
    const adj =
      Math.abs(fin.injury_effect ?? 0) +
      Math.abs(fin.squad_effect ?? 0) +
      Math.abs(fin.upset_effect ?? 0) +
      Math.abs(fin.odds_effect ?? 0);
    if (adj < 0.08) {
      reasons.push("No major pre-match intelligence adjustment");
      score += 1;
    } else {
      reasons.push("Pre-match intelligence layer applied — wider uncertainty");
      score -= 1;
    }
  } else {
    reasons.push("Base model probabilities (no live match intelligence row)");
  }

  const level = score >= 3 ? "High" : score >= 1 ? "Medium" : "Low";
  return { level, reasons };
}

export function confidenceEmoji(level: string): string {
  if (level === "High") return "🟢";
  if (level === "Medium") return "🟡";
  if (level === "Low") return "🔴";
  return "⚪";
}
