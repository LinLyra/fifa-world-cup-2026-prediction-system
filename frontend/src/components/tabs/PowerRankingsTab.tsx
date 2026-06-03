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
import type { IntelligenceRow } from "../../types";
import DataTable from "../DataTable";
import Section from "../Section";
import { formatMarketValue, pct } from "../../utils/format";

type Props = { intelligence: IntelligenceRow[] };

export default function PowerRankingsTab({ intelligence }: Props) {
  const top = [...intelligence].sort((a, b) => b.intelligence_score_v2 - a.intelligence_score_v2).slice(0, 30);

  return (
    <Section
      title="💪 Power Rankings"
      tagline="How strong is every team entering the tournament?"
    >
      <div className="mb-6 rounded-xl border border-[#E0E8E3] bg-white p-4">
        <ResponsiveContainer width="100%" height={420}>
          <ScatterChart margin={{ top: 16, right: 24, bottom: 24, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E0E8E3" />
            <XAxis type="number" dataKey="attack_rating" name="Attack" label={{ value: "Attack Rating", position: "insideBottom", offset: -8 }} />
            <YAxis type="number" dataKey="defense_rating" name="Defense" label={{ value: "Defense Rating", angle: -90, position: "insideLeft" }} />
            <ZAxis type="number" dataKey="intelligence_score_v2" range={[60, 400]} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} content={({ payload }) => {
              if (!payload?.[0]?.payload) return null;
              const p = payload[0].payload as IntelligenceRow;
              return (
                <div className="rounded-lg border bg-white p-2 text-xs shadow">
                  <div className="font-semibold">{p.team}</div>
                  <div>Strength: {p.intelligence_score_v2.toFixed(3)}</div>
                </div>
              );
            }} />
            <Scatter data={top} fill="#1B5E20" fillOpacity={0.75} />
          </ScatterChart>
        </ResponsiveContainer>
        <p className="text-center text-xs text-[#555]">Team Strength Landscape — Attack vs Defense (top 30)</p>
      </div>

      <DataTable
        columns={["Team", "Elo", "Squad Value", "Market Title Prob", "Strength Score", "Attack", "Defense"]}
        rows={top.map((t) => ({
          Team: t.team,
          Elo: Math.round(t.elo),
          "Squad Value": formatMarketValue(t.market_value_eur),
          "Market Title Prob": pct(t.market_champion_prob, 1),
          "Strength Score": t.intelligence_score_v2.toFixed(3),
          Attack: t.attack_rating.toFixed(2),
          Defense: t.defense_rating.toFixed(2),
        }))}
      />
    </Section>
  );
}
