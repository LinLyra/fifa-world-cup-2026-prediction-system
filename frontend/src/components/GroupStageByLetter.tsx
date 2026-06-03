import type { BracketMatch, FixtureRow, GroupRow } from "../types";
import TeamFlag from "./TeamFlag";
import { buildGroupLetterBlocks, type GroupLetterBlock } from "../utils/groupBracketReference";
import { pct } from "../utils/format";

type Props = {
  fixtures: FixtureRow[];
  groups: GroupRow[];
  /** When set, show which teams appear in the consensus R32 draw and their slot. */
  r32Matches?: BracketMatch[];
  title?: string;
  compact?: boolean;
};

function GroupCard({ block, showBracket }: { block: GroupLetterBlock; showBracket: boolean }) {
  return (
    <div className="rounded-lg border border-[#E0E8E3] bg-white p-3 shadow-sm">
      <h4 className="mb-2 text-sm font-bold text-[#1B5E20]">Group {block.letter}</h4>
      <ul className="space-y-2">
        {block.teams.map((t) => (
          <li key={t.team} className="text-xs text-[#333]">
            <div className="flex items-center gap-1.5">
              <TeamFlag team={t.team} size={16} />
              <span className="font-semibold">{t.team}</span>
            </div>
            <div className="mt-0.5 pl-5 text-[11px] text-[#666]">
              Win {pct(t.groupWinnerProb, 0)} · Top 2 {pct(t.top2Prob, 0)} · Advance {pct(t.advanceProb, 0)}
            </div>
            {showBracket && (
              <div
                className={`mt-0.5 pl-5 text-[11px] ${t.bracketRole ? "font-medium text-sky-800" : "text-[#999]"}`}
              >
                {t.bracketRole ?? "Not in this R32 draw"}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function GroupStageByLetter({ fixtures, groups, r32Matches, title, compact }: Props) {
  const blocks = buildGroupLetterBlocks(
    fixtures,
    groups,
    r32Matches ?? []
  );
  const showBracket = Boolean(r32Matches?.length);

  return (
    <div className={compact ? "" : "mt-6"}>
      {title && <h3 className="mb-2 text-base font-bold text-[#111]">{title}</h3>}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {blocks.map((b) => (
          <GroupCard key={b.letter} block={b} showBracket={showBracket} />
        ))}
      </div>
    </div>
  );
}
