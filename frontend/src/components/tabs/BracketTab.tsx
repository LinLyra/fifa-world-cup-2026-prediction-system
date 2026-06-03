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
    <Section title="🌳 Bracket" tagline="Consensus knockout pathway from 20,000 full-tournament simulations.">
      <h3 className="mb-3 text-base font-bold text-[#111]">Consensus Knockout Bracket</h3>
      <p className="mb-2 text-sm leading-relaxed text-[#555]">
        This bracket represents the most probable knockout pathway derived from 20,000 World Cup simulations.
      </p>
      <p className="mb-2 text-sm leading-relaxed text-[#555]">
        Each matchup reflects the most frequently occurring pairing at that stage, together with the model&apos;s
        estimated win probability.
      </p>
      <p className="mb-3 text-sm leading-relaxed text-[#555]">
        It is not a single simulated tournament, but a consensus view of how the tournament is most likely to unfold.
      </p>
      <p className="mb-1 text-sm font-medium text-[#333]">
        Select a team to highlight its projected route to the trophy.
      </p>
      <p className="mb-4 text-xs text-[#777]">
        Use <strong>Fit</strong>, drag, or <strong>+/−</strong> to navigate the full bracket. The complete tree is in
        the expander when a team is selected.
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
