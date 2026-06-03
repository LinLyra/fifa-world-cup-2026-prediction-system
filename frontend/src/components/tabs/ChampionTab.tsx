import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChampionRow } from "../../types";
import DataTable from "../DataTable";
import Section from "../Section";
import { CHAMPION_MIN_PROB, CHAMPION_TOP_N, COLORS, pct } from "../../utils/format";

type Props = { champions: ChampionRow[] };

export default function ChampionTab({ champions }: Props) {
  const pool = champions
    .filter((c) => c.champion_prob >= CHAMPION_MIN_PROB)
    .sort((a, b) => b.champion_prob - a.champion_prob);
  const contenders = (pool.length ? pool : [...champions].sort((a, b) => b.champion_prob - a.champion_prob)).slice(
    0,
    CHAMPION_TOP_N
  );
  const chartData = contenders.map((c) => ({
    team: c.team,
    prob: c.champion_prob,
    label: pct(c.champion_prob, 2),
  }));

  return (
    <Section
      title="🏆 Who Wins the World Cup?"
      tagline="Title probabilities from 20,000 full-tournament simulations."
    >
      <p className="mb-4 text-sm text-[#555]">
        Top {contenders.length} title contenders (≥{pct(CHAMPION_MIN_PROB, 1)} shown when available). Chart and
        table use the same ranking.
      </p>
      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <div className="rounded-xl border border-[#E0E8E3] bg-white p-4">
            <h3 className="mb-3 text-sm font-semibold text-[#111]">
              Top {contenders.length} — Title Probability
            </h3>
            <ResponsiveContainer width="100%" height={Math.max(380, contenders.length * 32)}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 48, top: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E0E8E3" horizontal={false} />
                <XAxis type="number" tickFormatter={(v) => pct(v, 0)} domain={[0, "auto"]} />
                <YAxis type="category" dataKey="team" width={110} tick={{ fontSize: 12 }} reversed />
                <Tooltip formatter={(v: number) => pct(v, 2)} />
                <Bar dataKey="prob" fill={COLORS.gold} radius={[0, 4, 4, 0]} label={{ position: "right", formatter: (v: number) => pct(v, 2) }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="lg:col-span-2">
          <DataTable
            columns={["Team", "Title Prob", "Simulated Titles"]}
            rows={contenders.map((c) => ({
              Team: c.team,
              "Title Prob": pct(c.champion_prob, 2),
              "Simulated Titles": c.titles,
            }))}
          />
        </div>
      </div>
    </Section>
  );
}
