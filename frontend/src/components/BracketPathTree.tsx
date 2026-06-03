import { useMemo, useState } from "react";
import type { ReachProbRow } from "../types";
import BracketZoomCanvas from "./BracketZoomCanvas";
import TeamFlag from "./TeamFlag";
import {
  LEFT_QF,
  LEFT_R16,
  LEFT_R32,
  LEFT_SF,
  RIGHT_QF,
  RIGHT_R16,
  RIGHT_R32,
  RIGHT_SF,
  pathChainOrdered,
  roundShortLabel,
  traceTeamPath,
} from "../utils/bracketPath";

export type BracketMatch = {
  match_id: number;
  round: string;
  side: string;
  home: string;
  away: string;
  winner: string;
  p_home: number;
  p_away: number;
  x: number;
  y: number;
};

export type BracketLink = {
  to: number;
  from_a: number;
  from_b: number;
};

export type BracketData = {
  matches: BracketMatch[];
  links: BracketLink[];
  champion_probs: Record<string, number>;
  path_difficulty: Record<string, number>;
  flags?: Record<string, string>;
};

type Props = {
  data: BracketData;
  reachProbs?: ReachProbRow[];
};

function MatchCard({
  m,
  activeTeam,
  onPath,
  dimmed,
  onHover,
  championProb,
}: {
  m: BracketMatch;
  activeTeam: string | null;
  onPath: boolean;
  dimmed: boolean;
  onHover: (m: BracketMatch) => void;
  championProb?: number;
}) {
  const homeWin = m.winner === m.home;
  const awayWin = m.winner === m.away;
  const homeHigher = m.p_home >= m.p_away;
  const top = homeHigher
    ? { name: m.home, p: m.p_home, win: homeWin, tracked: activeTeam === m.home }
    : { name: m.away, p: m.p_away, win: awayWin, tracked: activeTeam === m.away };
  const bottom = homeHigher
    ? { name: m.away, p: m.p_away, win: awayWin, tracked: activeTeam === m.away }
    : { name: m.home, p: m.p_home, win: homeWin, tracked: activeTeam === m.home };

  const row = (t: typeof top) => (
    <div
      className={`flex items-center gap-2 rounded-md px-1 py-1 ${
        t.win ? "bg-blue-500/25 ring-1 ring-blue-500" : ""
      } ${t.tracked ? "ring-1 ring-amber-400" : ""}`}
    >
      <TeamFlag team={t.name} size={20} />
      <span className="flex-1 text-xs font-semibold text-slate-100">{t.name}</span>
      <span className="text-xs text-slate-400">{(t.p * 100).toFixed(1)}%</span>
    </div>
  );

  return (
    <div
      className={`rounded-lg border-2 px-2.5 py-2 transition-all ${
        onPath
          ? "border-sky-400 bg-sky-950/60 shadow-md shadow-sky-500/20"
          : "border-slate-600 bg-slate-900"
      } ${dimmed ? "opacity-30" : "opacity-100"}`}
      onMouseEnter={() => onHover(m)}
    >
      {row(top)}
      <div className="my-0.5 text-center text-[10px] font-extrabold tracking-wider text-slate-500">VS</div>
      {row(bottom)}
      {championProb !== undefined && m.match_id === 104 && (
        <p className="mt-2 text-center text-xs text-amber-200">
          <TeamFlag team={m.winner} size={16} className="mr-1 inline-block align-middle" />
          <strong>{m.winner}</strong> · {(championProb * 100).toFixed(1)}% title
        </p>
      )}
    </div>
  );
}

function RoundColumn({
  label,
  ids,
  byId,
  activeTeam,
  pathIds,
  focusOnly,
  onHover,
  slotMargin,
}: {
  label: string;
  ids: number[];
  byId: Record<number, BracketMatch>;
  activeTeam: string | null;
  pathIds: Set<number>;
  focusOnly: boolean;
  onHover: (m: BracketMatch) => void;
  slotMargin?: number[];
}) {
  const slots = ids
    .map((id, i) => {
      const m = byId[id];
      if (!m) return null;
      if (focusOnly && activeTeam && !pathIds.has(id)) return null;
      const onPath = pathIds.has(id);
      const dimmed = Boolean(activeTeam && !onPath);
      const mt = slotMargin?.[i] ?? 0;
      return (
        <div key={id} style={{ marginTop: mt }} className="mb-1.5">
          <MatchCard
            m={m}
            activeTeam={activeTeam}
            onPath={onPath}
            dimmed={dimmed}
            onHover={onHover}
          />
        </div>
      );
    })
    .filter(Boolean);

  if (focusOnly && activeTeam && slots.length === 0) return null;

  return (
    <div className="min-w-[188px] shrink-0">
      <div className="mb-2 text-center text-[11px] font-bold uppercase tracking-widest text-slate-400">{label}</div>
      {slots}
    </div>
  );
}

function FullBracketGrid({
  byId,
  activeTeam,
  pathIds,
  focusOnly,
  onHover,
  championProbs,
}: {
  byId: Record<number, BracketMatch>;
  activeTeam: string | null;
  pathIds: Set<number>;
  focusOnly: boolean;
  onHover: (m: BracketMatch) => void;
  championProbs: Record<string, number>;
}) {
  const final = byId[104];
  const r32Gap = 8;
  const r16Gap = 52;
  const qfGap = 120;
  const sfGap = 280;
  const r32Margins = [0, ...Array(7).fill(r32Gap)];

  const col = (label: string, ids: number[], margin?: number[]) => (
    <RoundColumn
      label={label}
      ids={ids}
      byId={byId}
      activeTeam={activeTeam}
      pathIds={pathIds}
      focusOnly={focusOnly}
      onHover={onHover}
      slotMargin={margin}
    />
  );

  return (
    <div className="bracket-grid inline-flex min-w-max items-stretch justify-center gap-2.5 py-2">
      {/* Left: R32 (outer) → SF (toward final) */}
      <div className="bracket-side-left flex gap-2">
        {col("R32", LEFT_R32, r32Margins)}
        {col("R16", LEFT_R16, [r16Gap, r16Gap * 3, r16Gap * 3, r16Gap * 3])}
        {col("QF", LEFT_QF, [qfGap, qfGap * 3])}
        {col("SF", LEFT_SF, [sfGap])}
      </div>

      {final && (
        <div className="mt-[120px] flex w-[200px] shrink-0 flex-col items-center px-2">
          <div className="mb-3 text-lg font-extrabold text-amber-400">🏆 FINAL</div>
          <MatchCard
            m={final}
            activeTeam={activeTeam}
            onPath={pathIds.has(104)}
            dimmed={Boolean(activeTeam && !pathIds.has(104))}
            onHover={onHover}
            championProb={championProbs[final.winner]}
          />
        </div>
      )}

      {/* Right: SF (toward final) → R32 (outer edge), mirrors Streamlit */}
      <div className="bracket-side-right flex gap-2">
        {col("SF", RIGHT_SF, [sfGap])}
        {col("QF", RIGHT_QF, [qfGap, qfGap * 3])}
        {col("R16", RIGHT_R16, [r16Gap, r16Gap * 3, r16Gap * 3, r16Gap * 3])}
        {col("R32", RIGHT_R32, r32Margins)}
      </div>
    </div>
  );
}

function JourneyLane({
  chain,
  activeTeam,
  pathIds,
  onHover,
}: {
  chain: BracketMatch[];
  activeTeam: string;
  pathIds: Set<number>;
  onHover: (m: BracketMatch) => void;
}) {
  if (!chain.length) {
    return (
      <p className="rounded-lg border border-amber-500/40 bg-amber-950/30 p-4 text-sm text-amber-100">
        <strong>{activeTeam}</strong> does not appear on the consensus Round of 32 draw.
      </p>
    );
  }

  const stops = chain.map((m) => roundShortLabel(m.round)).join(" → ");

  return (
    <div>
      <p className="mb-3 text-sm text-slate-300">
        Most probable knockout route for <TeamFlag team={activeTeam} size={18} className="mr-1 inline-block align-middle" />{" "}
        <strong className="text-amber-300">{activeTeam}</strong> — stops when the model favours an opponent.
        <br />
        <span className="text-sky-400">{stops}</span>
      </p>
      <div className="overflow-x-auto pb-2">
        <div className="flex min-w-max items-center gap-2">
          {chain.map((m, i) => (
            <div key={m.match_id} className="flex items-center gap-2">
              {i > 0 && <span className="text-2xl font-bold text-sky-500">→</span>}
              <div className="w-[188px] shrink-0">
                <div className="mb-1 text-center text-[10px] font-bold uppercase text-slate-500">
                  {roundShortLabel(m.round)}
                </div>
                <MatchCard
                  m={m}
                  activeTeam={activeTeam}
                  onPath={pathIds.has(m.match_id)}
                  dimmed={false}
                  onHover={onHover}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function BracketPathTree({ data, reachProbs = [] }: Props) {
  const [activeTeam, setActiveTeam] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState("");

  const byId = useMemo(
    () => Object.fromEntries(data.matches.map((m) => [m.match_id, m])),
    [data.matches]
  );

  const teams = useMemo(() => {
    const s = new Set<string>();
    data.matches.forEach((m) => {
      s.add(m.home);
      s.add(m.away);
      s.add(m.winner);
    });
    return Array.from(s).sort();
  }, [data.matches]);

  const pathIds = useMemo(
    () => traceTeamPath(data.matches, data.links, activeTeam),
    [data.matches, data.links, activeTeam]
  );

  const pathChain = useMemo(
    () => pathChainOrdered(data.matches, pathIds),
    [data.matches, pathIds]
  );

  const onHoverNode = (m: BracketMatch) => {
    const pWin = m.winner === m.home ? m.p_home : m.p_away;
    const title = data.champion_probs[m.winner] ?? 0;
    const path = data.path_difficulty[m.winner];
    const pathTxt = path !== undefined && !Number.isNaN(path) ? path.toFixed(2) : "—";
    setTooltip(
      `${m.home} vs ${m.away} → ${m.winner} | KO ${(pWin * 100).toFixed(1)}% | Title ${(title * 100).toFixed(1)}% | Path ${pathTxt}`
    );
  };

  const final = byId[104];
  const reach = activeTeam ? reachProbs.find((x) => x.team === activeTeam) : null;

  return (
    <div className="w-full rounded-xl bg-gradient-to-b from-slate-950 to-slate-900 p-4 shadow-xl ring-1 ring-slate-700">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label className="text-sm text-slate-300">Most Probable Knockout Journey</label>
        <select
          className="max-w-xs rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100"
          value={activeTeam ?? ""}
          onChange={(e) => setActiveTeam(e.target.value || null)}
        >
          <option value="">— Full bracket (no team selected) —</option>
          {teams.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {activeTeam && (
        <div className="mb-4 rounded-lg border border-sky-500/30 bg-sky-950/40 p-3 text-sm text-slate-200">
          Highlighted route = the <strong>most likely knockout path</strong> for this team on the consensus bracket.
          It is <strong>not</strong> a guaranteed route or a title prediction.
        </div>
      )}

      {reach && (
        <div className="mb-4 grid grid-cols-3 gap-2 md:grid-cols-6">
          {(
            [
              ["Reach R32", reach.reach_r32],
              ["Reach R16", reach.reach_r16],
              ["Reach QF", reach.reach_qf],
              ["Reach SF", reach.reach_sf],
              ["Reach Final", reach.reach_final],
              ["Win World Cup", reach.reach_win],
            ] as const
          ).map(([label, val]) => (
            <div key={label} className="rounded-lg bg-slate-800/80 px-2 py-2 text-center">
              <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
              <div className="text-sm font-bold text-slate-100">{(val * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      )}

      {tooltip && (
        <p className="mb-3 rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-200 ring-1 ring-blue-500/40">{tooltip}</p>
      )}

      {activeTeam ? (
        <>
          <JourneyLane
            chain={pathChain}
            activeTeam={activeTeam}
            pathIds={pathIds}
            onHover={onHoverNode}
          />

          <details className="mt-4">
            <summary className="cursor-pointer text-sm font-semibold text-sky-400 hover:text-sky-300">
              View full consensus bracket (all teams)
            </summary>
            <div className="mt-3">
              <BracketZoomCanvas height={520}>
                <FullBracketGrid
                  byId={byId}
                  activeTeam={activeTeam}
                  pathIds={pathIds}
                  focusOnly={false}
                  onHover={onHoverNode}
                  championProbs={data.champion_probs}
                />
              </BracketZoomCanvas>
            </div>
          </details>
        </>
      ) : (
        <BracketZoomCanvas height={600}>
          <FullBracketGrid
            byId={byId}
            activeTeam={null}
            pathIds={new Set()}
            focusOnly={false}
            onHover={onHoverNode}
            championProbs={data.champion_probs}
          />
        </BracketZoomCanvas>
      )}

      {final && !activeTeam && (
        <p className="mt-3 text-center text-xs text-slate-500">
          Consensus final: {final.home} vs {final.away} → {final.winner} (
          {((data.champion_probs[final.winner] ?? 0) * 100).toFixed(1)}% title)
        </p>
      )}
    </div>
  );
}
