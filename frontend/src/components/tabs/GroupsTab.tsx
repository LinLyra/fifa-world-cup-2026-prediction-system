import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { FixtureRow, GroupRow } from "../../types";
import DataTable from "../DataTable";
import GroupStageByLetter from "../GroupStageByLetter";
import Section from "../Section";
import { COLORS, pct } from "../../utils/format";

type Props = { groups: GroupRow[]; fixtures: FixtureRow[] };

export default function GroupsTab({ groups, fixtures }: Props) {
  const ranked = [...groups].sort((a, b) => b.advance_prob - a.advance_prob);
  const top = ranked.slice(0, 15);
  const chartData = top.map((g) => ({
    team: g.team,
    "Group Winner": g.group_winner_prob,
    "Top 2": g.group_top2_prob,
    Advance: g.advance_prob,
  }));

  return (
    <Section
      title="📊 Who Survives the Group Stage?"
      tagline="Advance probabilities including best third-place routes."
    >
      <div className="mb-6 rounded-xl border border-[#E0E8E3] bg-white p-4">
        <ResponsiveContainer width="100%" height={460}>
          <BarChart data={chartData} margin={{ bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E0E8E3" />
            <XAxis dataKey="team" angle={-45} textAnchor="end" interval={0} height={80} tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={(v) => pct(v, 0)} />
            <Tooltip formatter={(v: number) => pct(v, 1)} />
            <Legend verticalAlign="top" />
            <Bar dataKey="Group Winner" fill={COLORS.pitch} />
            <Bar dataKey="Top 2" fill={COLORS.pitchLight} />
            <Bar dataKey="Advance" fill={COLORS.gold} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <details className="mb-6 rounded-lg border border-[#E0E8E3] bg-[#F7F9F8] px-4 py-3" open>
        <summary className="cursor-pointer text-sm font-semibold text-[#1B5E20]">
          Groups A–L (four teams per group)
        </summary>
        <p className="mt-2 text-xs text-[#666]">
          Model probabilities only — no knockout draw. See the Bracket tab for who appears in the consensus Round of
          32.
        </p>
        <GroupStageByLetter fixtures={fixtures} groups={groups} title="" compact />
      </details>

      <h3 className="mb-2 text-base font-bold text-[#111]">Group Qualification — All Teams (ranked)</h3>
      <DataTable
        columns={["Team", "Group Winner", "Top 2", "Advance"]}
        rows={ranked.map((g) => ({
          Team: g.team,
          "Group Winner": pct(g.group_winner_prob, 1),
          "Top 2": pct(g.group_top2_prob, 1),
          Advance: pct(g.advance_prob, 1),
        }))}
      />
    </Section>
  );
}
