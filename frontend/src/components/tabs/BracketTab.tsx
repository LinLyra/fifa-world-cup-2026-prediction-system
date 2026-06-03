import type { BracketData, ChampionRow, ReachProbRow } from "../../types";
import BracketPathTree from "../BracketPathTree";
import Section from "../Section";
import { pct } from "../../utils/format";

type Props = {
  bracket: BracketData;
  reachProbs: ReachProbRow[];
};

export default function BracketTab({ bracket, reachProbs }: Props) {
  const final = bracket.matches.find((m) => m.match_id === 104);

  return (
    <Section title="🌳 Bracket" tagline="What is each team's path to the trophy?">
      <h3 className="mb-1 text-base font-bold text-[#111]">Consensus Knockout Bracket</h3>
      <p className="mb-1 text-sm text-[#555]">
        Single most-likely tournament tree from the modal Round of 32 draw and model win probabilities. This is{" "}
        <strong>not</strong> every parallel simulation — it is one readable reference bracket.
      </p>
      <p className="mb-4 text-sm text-[#555]">
        Use <strong>Fit</strong>, drag, scroll, or <strong>+/−</strong> on the full bracket. Select a team to see their
        knockout journey as a separate path (full bracket stays in the expander below).
      </p>

      <BracketPathTree data={bracket} reachProbs={reachProbs} />

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
