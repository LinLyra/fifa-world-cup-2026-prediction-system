import type { BracketData, FixtureRow, GroupRow, ReachProbRow } from "../../types";
import BracketPathTree from "../BracketPathTree";
import GroupStageByLetter from "../GroupStageByLetter";
import Section from "../Section";
import { pct } from "../../utils/format";

type Props = {
  bracket: BracketData;
  reachProbs: ReachProbRow[];
  groups: GroupRow[];
  fixtures: FixtureRow[];
};

export default function BracketTab({ bracket, reachProbs, groups, fixtures }: Props) {
  const final = bracket.matches.find((m) => m.match_id === 104);
  const r32 = bracket.matches.filter((m) => m.round === "Round of 32");

  return (
    <Section title="🌳 Bracket" tagline="Consensus knockout pathway from 20,000 full-tournament simulations.">
      <h3 className="mb-3 text-base font-bold text-[#111]">Consensus Knockout Bracket</h3>
      <div className="mb-4 rounded-lg border border-amber-200/80 bg-amber-50/90 px-3 py-3 text-sm leading-relaxed text-amber-950">
        <p className="font-semibold">Why might a team with low group-win % still appear in Round of 32?</p>
        <p className="mt-1">
          The tree uses the <strong>single most frequent complete R32 draw</strong> across 20,000 simulations — not the
          same as &quot;who is most likely to win each group&quot; on the Groups tab. Rare outcomes can appear if they
          often co-occur with other slots (e.g. a best-third place from another group). Use the reference below to map{" "}
          <strong>Group A–L → teams → this draw</strong>.
        </p>
      </div>
      <p className="mb-2 text-sm leading-relaxed text-[#555]">
        Round of 32 = that joint-modal draw (32 unique teams). Round of 16 onward = model KO win % on this fixed path.
      </p>
      <p className="mb-3 text-sm leading-relaxed text-[#555]">
        Match labels are <strong>KO win %</strong>, not group advance %. Same advance data as the Groups tab; bracket
        only adds <strong>who is in this draw</strong> and their FIFA slot.
      </p>
      <p className="mb-4 text-sm font-medium text-[#333]">
        Select a team to highlight its projected route to the trophy.
      </p>

      <BracketPathTree data={bracket} reachProbs={reachProbs} />

      <div className="mt-8 border-t border-[#E0E8E3] pt-6">
        <h3 className="mb-1 text-base font-bold text-[#111]">Groups A–L and this Round of 32 draw</h3>
        <p className="mb-4 text-xs text-[#666]">
          Win / Top 2 / Advance match the Groups tab. Lines in blue show who is in this bracket only (half + match id).
        </p>
        <GroupStageByLetter fixtures={fixtures} groups={groups} r32Matches={r32} compact />
      </div>

      {final && (
        <p className="mt-4 text-sm text-[#555]">
          Consensus final pairing: <strong>{final.home}</strong> vs <strong>{final.away}</strong> (model KO edge{" "}
          <strong>{final.winner}</strong> {pct(Math.max(final.p_home, final.p_away), 0)}). See Champion tab for title
          probabilities.
        </p>
      )}
    </Section>
  );
}
