import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { ChampionRow, PathDifficultyRow } from "../../types";
import DataTable from "../DataTable";
import Section from "../Section";
import {
  CHAMPION_MIN_PROB,
  PATH_TABLE_TOP_N,
  SIMULATIONS,
  championProbForTeam,
  pathDifficultyLabel,
  pct,
} from "../../utils/format";

type Props = {
  pathDifficulty: PathDifficultyRow[];
  champions: ChampionRow[];
};

export default function PathDifficultyTab({ pathDifficulty, champions }: Props) {
  const plot = pathDifficulty
    .map((row) => ({
      ...row,
      champion_prob: championProbForTeam(row.team, row, champions),
    }))
    .filter((r) => r.expected_path_difficulty != null && !Number.isNaN(r.expected_path_difficulty));

  const tableRows = [...plot]
    .sort((a, b) => (b.champion_prob ?? 0) - (a.champion_prob ?? 0))
    .filter((r) => (r.champion_prob ?? 0) >= CHAMPION_MIN_PROB)
    .slice(0, PATH_TABLE_TOP_N);

  const displayRows =
    tableRows.length > 0
      ? tableRows
      : [...plot].sort((a, b) => (b.champion_prob ?? 0) - (a.champion_prob ?? 0)).slice(0, PATH_TABLE_TOP_N);

  return (
    <Section title="🛤️ Path Difficulty" tagline="How hard is each team's route to the trophy?">
      <h3 className="mb-1 text-base font-bold text-[#111]">Path Difficulty vs Title Chance</h3>
      <p className="mb-4 text-sm text-[#555]">
        Higher path difficulty = tougher expected opponents on the knockout route. Bubble size reflects title
        probability (same {SIMULATIONS.toLocaleString()} simulations as the Champion tab).
      </p>

      <div className="mb-8 rounded-xl border border-[#E0E8E3] bg-white p-4">
        <ResponsiveContainer width="100%" height={380}>
          <ScatterChart margin={{ top: 16, right: 24, bottom: 24, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E0E8E3" />
            <XAxis
              type="number"
              dataKey="expected_path_difficulty"
              name="Path Difficulty"
              label={{ value: "Path Difficulty", position: "insideBottom", offset: -8 }}
            />
            <YAxis
              type="number"
              dataKey="champion_prob"
              name="Title Probability"
              tickFormatter={(v) => pct(v, 0)}
              label={{ value: "Title Probability", angle: -90, position: "insideLeft" }}
            />
            <ZAxis type="number" dataKey="champion_prob" range={[40, 400]} />
            <Tooltip
              formatter={(v: number, name: string) =>
                name.includes("prob") || name.includes("Probability") ? pct(v, 2) : v.toFixed(2)
              }
              labelFormatter={(_, payload) => payload?.[0]?.payload?.team ?? ""}
            />
            <Scatter data={plot} fill="#1B5E20" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <h3 className="mb-1 text-base font-bold text-[#111]">Road to the Final</h3>
      <p className="mb-4 text-sm text-[#555]">Expected opponent strength on the most likely knockout path.</p>

      <DataTable
        columns={["Path Rank", "Team", "Title Prob", "Expected Opponent Strength", "Difficulty", "Rating"]}
        rows={displayRows.map((row, i) => {
          const [stars, tier] = pathDifficultyLabel(row.path_difficulty_percentile);
          return {
            "Path Rank": i + 1,
            Team: row.team,
            "Title Prob": row.champion_prob != null ? pct(row.champion_prob, 1) : "—",
            "Expected Opponent Strength": row.expected_path_difficulty?.toFixed(2) ?? "—",
            Difficulty: tier,
            Rating: stars,
          };
        })}
      />
    </Section>
  );
}
