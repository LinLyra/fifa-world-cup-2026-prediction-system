import { useEffect, useState } from "react";
import type { DashboardData } from "../types";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Missing ${path} — run: python scripts/export_dashboard_json.py`);
  return res.json();
}

export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const [
          meta,
          champions,
          groups,
          intelligence,
          pathDifficulty,
          matchMatrix,
          finalIntel,
          reachProbs,
          bracket,
        ] = await Promise.all([
          fetchJson<import("../types").Meta>("/data/meta.json"),
          fetchJson<import("../types").ChampionRow[]>("/data/champions.json"),
          fetchJson<import("../types").GroupRow[]>("/data/groups.json"),
          fetchJson<import("../types").IntelligenceRow[]>("/data/intelligence.json"),
          fetchJson<import("../types").PathDifficultyRow[]>("/data/path_difficulty.json"),
          fetchJson<import("../types").MatchMatrixRow[]>("/data/match_matrix.json"),
          fetchJson<import("../types").FinalIntelRow[]>("/data/final_match_intel.json"),
          fetchJson<import("../types").ReachProbRow[]>("/data/reach_probs.json"),
          fetchJson<import("../types").BracketData>("/data/bracket_consensus.json"),
        ]);

        if (!cancelled) {
          setData({
            meta,
            champions,
            groups,
            intelligence,
            pathDifficulty,
            matchMatrix,
            finalIntel,
            reachProbs,
            bracket,
          });
        }
      } catch (e) {
        if (!cancelled) setError(String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return { data, error, loading };
}
