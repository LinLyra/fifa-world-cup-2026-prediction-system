import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { FinalIntelRow, IntelligenceRow, MatchMatrixRow } from "../../types";
import Section from "../Section";
import { COLORS, parseScorelines, pct } from "../../utils/format";
import { confidenceEmoji, modelConfidence } from "../../utils/modelConfidence";

type Props = {
  matchMatrix: MatchMatrixRow[];
  finalIntel: FinalIntelRow[];
  intelligence: IntelligenceRow[];
  teams: string[];
};

export default function MatchupsTab({ matchMatrix, finalIntel, intelligence, teams }: Props) {
  const ranked = useMemo(
    () => [...intelligence].sort((a, b) => b.intelligence_score_v2 - a.intelligence_score_v2),
    [intelligence]
  );
  const defaultA = ranked[0]?.team ?? teams[0];
  const defaultB = ranked[1]?.team ?? teams[1];

  const [teamA, setTeamA] = useState(defaultA);
  const [teamB, setTeamB] = useState(defaultB !== defaultA ? defaultB : teams.find((t) => t !== defaultA) ?? defaultB);

  const others = teams.filter((t) => t !== teamA);
  const row = matchMatrix.find((m) => m.home_team === teamA && m.away_team === teamB);
  const fin = finalIntel.find((m) => m.home_team === teamA && m.away_team === teamB) ?? null;

  const confidence = row ? modelConfidence(teamA, teamB, row, intelligence, fin) : null;
  const homeXg = fin?.final_home_xg ?? row?.expected_home_goals;
  const awayXg = fin?.final_away_xg ?? row?.expected_away_goals;

  return (
    <Section title="⚔️ Matchup Explorer" tagline="What happens if Team A plays Team B?">
      <div className="mb-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-[#111]">
          Team A (Home)
          <select
            className="mt-1 w-full rounded-lg border border-[#E0E8E3] bg-white px-3 py-2"
            value={teamA}
            onChange={(e) => {
              setTeamA(e.target.value);
              if (e.target.value === teamB) {
                const alt = teams.find((t) => t !== e.target.value);
                if (alt) setTeamB(alt);
              }
            }}
          >
            {teams.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-medium text-[#111]">
          Team B (Away)
          <select
            className="mt-1 w-full rounded-lg border border-[#E0E8E3] bg-white px-3 py-2"
            value={teamB}
            onChange={(e) => setTeamB(e.target.value)}
          >
            {others.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </div>

      {!row ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          No pre-computed row for <strong>{teamA}</strong> vs <strong>{teamB}</strong> (home/away).
        </p>
      ) : (
        <>
          {confidence && (
            <div className="mb-4 rounded-lg border border-[#E0E8E3] bg-white p-4 text-sm">
              <p className="font-semibold">
                Model Confidence: {confidenceEmoji(confidence.level)} {confidence.level}
              </p>
              <ul className="mt-2 list-disc pl-5 text-[#555]">
                {confidence.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              [`${teamA} xG`, homeXg?.toFixed(2) ?? "—"],
              [`${teamB} xG`, awayXg?.toFixed(2) ?? "—"],
              ["Most Likely Score", `${row.pred_home_score}–${row.pred_away_score}`],
              ["Scoreline Prob", pct(row.score_probability, 1)],
            ].map(([label, value]) => (
              <div key={label} className="metric-card">
                <div className="label">{label}</div>
                <div className="value">{value}</div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-[#E0E8E3] bg-white p-4">
              <h3 className="mb-3 text-sm font-semibold">Match Outcome Probabilities</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={[
                    { outcome: `${teamA} Win`, prob: row.home_win_prob, color: COLORS.pitch },
                    { outcome: "Draw", prob: row.draw_prob, color: COLORS.draw },
                    { outcome: `${teamB} Win`, prob: row.away_win_prob, color: COLORS.away },
                  ]}
                  margin={{ top: 24, right: 16, left: 8, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#E0E8E3" />
                  <XAxis dataKey="outcome" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 0.8]} tickFormatter={(v) => pct(v, 0)} />
                  <Tooltip formatter={(v: number) => pct(v, 2)} />
                  <Bar dataKey="prob" label={{ position: "top", formatter: (v: number) => pct(v, 2) }}>
                    {[COLORS.pitch, COLORS.draw, COLORS.away].map((c, i) => (
                      <Cell key={i} fill={c} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p className="text-xs text-[#555]">
                Home + Draw + Away = {pct(row.home_win_prob + row.draw_prob + row.away_win_prob, 2)} · Y-axis capped at
                80% for readability
              </p>
            </div>

            <div className="rounded-xl border border-[#E0E8E3] bg-white p-4">
              <h3 className="mb-3 text-sm font-semibold">Top 5 Scorelines</h3>
              {parseScorelines(row.top_5_scorelines).length ? (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    data={[...parseScorelines(row.top_5_scorelines)].reverse().map(([scoreline, prob]) => ({
                      scoreline,
                      prob,
                      label: pct(prob, 2),
                    }))}
                    layout="vertical"
                    margin={{ left: 8, right: 48 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E0E8E3" horizontal={false} />
                    <XAxis type="number" tickFormatter={(v) => pct(v, 0)} />
                    <YAxis type="category" dataKey="scoreline" width={48} />
                    <Tooltip formatter={(v: number) => pct(v, 2)} />
                    <Bar dataKey="prob" fill={COLORS.gold} label={{ position: "right", formatter: (v: number) => pct(v, 2) }} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-[#555]">Top scorelines unavailable for this matchup.</p>
              )}
            </div>
          </div>
        </>
      )}
    </Section>
  );
}
