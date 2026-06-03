import { useMemo, useState } from "react";
import type { ReachProbRow } from "../types";

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

const DEFAULT_FLAGS: Record<string, string> = {
  Algeria: "🇩🇿",
  Argentina: "🇦🇷",
  Australia: "🇦🇺",
  Austria: "🇦🇹",
  Belgium: "🇧🇪",
  "Bosnia and Herzegovina": "🇧🇦",
  Brazil: "🇧🇷",
  Canada: "🇨🇦",
  "Cape Verde": "🇨🇻",
  Colombia: "🇨🇴",
  Croatia: "🇭🇷",
  Curaçao: "🇨🇼",
  Czechia: "🇨🇿",
  "Democratic Republic of Congo": "🇨🇩",
  Ecuador: "🇪🇨",
  Egypt: "🇪🇬",
  England: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  France: "🇫🇷",
  Germany: "🇩🇪",
  Ghana: "🇬🇭",
  Haiti: "🇭🇹",
  Iran: "🇮🇷",
  Iraq: "🇮🇶",
  "Ivory Coast": "🇨🇮",
  Japan: "🇯🇵",
  Jordan: "🇯🇴",
  Mexico: "🇲🇽",
  Morocco: "🇲🇦",
  Netherlands: "🇳🇱",
  "New Zealand": "🇳🇿",
  Norway: "🇳🇴",
  Panama: "🇵🇦",
  Paraguay: "🇵🇾",
  Portugal: "🇵🇹",
  Qatar: "🇶🇦",
  "Saudi Arabia": "🇸🇦",
  Scotland: "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
  Senegal: "🇸🇳",
  "South Africa": "🇿🇦",
  "South Korea": "🇰🇷",
  Spain: "🇪🇸",
  Sweden: "🇸🇪",
  Switzerland: "🇨🇭",
  Tunisia: "🇹🇳",
  Turkey: "🇹🇷",
  "United States": "🇺🇸",
  Uruguay: "🇺🇾",
  Uzbekistan: "🇺🇿",
};

const LEFT_R32 = [73, 74, 76, 79, 81, 82, 86, 88];
const RIGHT_R32 = [75, 77, 78, 80, 83, 84, 85, 87];
const LEFT_R16 = [89, 90, 91, 92];
const RIGHT_R16 = [93, 94, 95, 96];
const LEFT_QF = [97, 98];
const RIGHT_QF = [99, 100];
const LEFT_SF = [101];
const RIGHT_SF = [102];

function teamInMatch(m: BracketMatch, team: string | null): boolean {
  if (!team) return false;
  return m.home === team || m.away === team || m.winner === team;
}

function MatchCard({
  m,
  active,
  flag,
  onHover,
}: {
  m: BracketMatch;
  active: boolean;
  flag: (t: string) => string;
  onHover: (m: BracketMatch) => void;
}) {
  const homeWin = m.winner === m.home;
  const awayWin = m.winner === m.away;
  return (
    <div
      className={`rounded-lg border-2 px-2.5 py-2 transition-colors ${
        active
          ? "border-blue-500 bg-blue-950/50"
          : "border-slate-600 bg-slate-900"
      }`}
      onMouseEnter={() => onHover(m)}
    >
      <div
        className={`flex items-center gap-2 rounded-md px-1 py-1 ${
          homeWin ? "bg-blue-500/25 ring-1 ring-blue-500" : ""
        }`}
      >
        <span className="text-xl leading-none">{flag(m.home)}</span>
        <span className="flex-1 text-xs font-semibold text-slate-100">
          {m.home}
        </span>
        <span className="text-xs text-slate-400">
          {(m.p_home * 100).toFixed(0)}%
        </span>
      </div>
      <div className="my-0.5 text-center text-[10px] font-extrabold tracking-wider text-slate-500">
        VS
      </div>
      <div
        className={`flex items-center gap-2 rounded-md px-1 py-1 ${
          awayWin ? "bg-blue-500/25 ring-1 ring-blue-500" : ""
        }`}
      >
        <span className="text-xl leading-none">{flag(m.away)}</span>
        <span className="flex-1 text-xs font-semibold text-slate-100">
          {m.away}
        </span>
        <span className="text-xs text-slate-400">
          {(m.p_away * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
}

function RoundColumn({
  label,
  ids,
  byId,
  activeTeam,
  flag,
  onHover,
  slotMargin,
}: {
  label: string;
  ids: number[];
  byId: Record<number, BracketMatch>;
  activeTeam: string | null;
  flag: (t: string) => string;
  onHover: (m: BracketMatch) => void;
  slotMargin?: number[];
}) {
  return (
    <div className="min-w-[200px]">
      <div className="mb-2 text-center text-[11px] font-bold uppercase tracking-widest text-slate-400">
        {label}
      </div>
      {ids.map((id, i) => {
        const m = byId[id];
        if (!m) return null;
        const mt = slotMargin?.[i] ?? 0;
        return (
          <div key={id} style={{ marginTop: mt }} className="mb-1.5">
            <MatchCard
              m={m}
              active={teamInMatch(m, activeTeam)}
              flag={flag}
              onHover={onHover}
            />
          </div>
        );
      })}
    </div>
  );
}

export default function BracketPathTree({ data, reachProbs = [] }: Props) {
  const [activeTeam, setActiveTeam] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<string>("");

  const flags = { ...DEFAULT_FLAGS, ...data.flags };

  const byId = useMemo(
    () => Object.fromEntries(data.matches.map((m) => [m.match_id, m])),
    [data.matches]
  );

  const flag = (t: string) => flags[t] ?? "🏳️";

  const teams = useMemo(() => {
    const s = new Set<string>();
    data.matches.forEach((m) => {
      s.add(m.home);
      s.add(m.away);
      s.add(m.winner);
    });
    return Array.from(s).sort();
  }, [data.matches]);

  const onHoverNode = (m: BracketMatch) => {
    const pWin = m.winner === m.home ? m.p_home : m.p_away;
    const title = data.champion_probs[m.winner] ?? 0;
    const path = data.path_difficulty[m.winner];
    const pathTxt =
      path !== undefined && !Number.isNaN(path) ? path.toFixed(2) : "—";
    setTooltip(
      `${flag(m.home)} ${m.home} vs ${flag(m.away)} ${m.away} → ${m.winner} | KO ${(pWin * 100).toFixed(0)}% | Title ${(title * 100).toFixed(1)}% | Path ${pathTxt}`
    );
  };

  const final = byId[104];
  const r32Gap = 8;
  const r16Gap = 52;
  const qfGap = 120;
  const sfGap = 280;
  const r32Margins = [0, ...Array(7).fill(r32Gap)];

  const leftSide = (
    <>
      <RoundColumn
        label="R32"
        ids={LEFT_R32}
        byId={byId}
        activeTeam={activeTeam}
        flag={flag}
        onHover={onHoverNode}
        slotMargin={r32Margins}
      />
      <RoundColumn
        label="R16"
        ids={LEFT_R16}
        byId={byId}
        activeTeam={activeTeam}
        flag={flag}
        onHover={onHoverNode}
        slotMargin={[r16Gap, r16Gap * 3, r16Gap * 3, r16Gap * 3]}
      />
      <RoundColumn
        label="QF"
        ids={LEFT_QF}
        byId={byId}
        activeTeam={activeTeam}
        flag={flag}
        onHover={onHoverNode}
        slotMargin={[qfGap, qfGap * 3]}
      />
      <RoundColumn
        label="SF"
        ids={LEFT_SF}
        byId={byId}
        activeTeam={activeTeam}
        flag={flag}
        onHover={onHoverNode}
        slotMargin={[sfGap]}
      />
    </>
  );

  const rightSide = (
    <>
      <RoundColumn
        label="SF"
        ids={RIGHT_SF}
        byId={byId}
        activeTeam={activeTeam}
        flag={flag}
        onHover={onHoverNode}
        slotMargin={[sfGap]}
      />
      <RoundColumn
        label="QF"
        ids={RIGHT_QF}
        byId={byId}
        activeTeam={activeTeam}
        flag={flag}
        onHover={onHoverNode}
        slotMargin={[qfGap, qfGap * 3]}
      />
      <RoundColumn
        label="R16"
        ids={RIGHT_R16}
        byId={byId}
        activeTeam={activeTeam}
        flag={flag}
        onHover={onHoverNode}
        slotMargin={[r16Gap, r16Gap * 3, r16Gap * 3, r16Gap * 3]}
      />
      <RoundColumn
        label="R32"
        ids={RIGHT_R32}
        byId={byId}
        activeTeam={activeTeam}
        flag={flag}
        onHover={onHoverNode}
        slotMargin={r32Margins}
      />
    </>
  );

  return (
    <div className="w-full rounded-xl bg-gradient-to-b from-slate-950 to-slate-900 p-4 shadow-xl ring-1 ring-slate-700">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label className="text-sm text-slate-300">Highlight team path</label>
        <select
          className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100"
          value={activeTeam ?? ""}
          onChange={(e) => setActiveTeam(e.target.value || null)}
        >
          <option value="">— Select team —</option>
          {teams.map((t) => (
            <option key={t} value={t}>
              {flag(t)} {t}
            </option>
          ))}
        </select>
        {activeTeam && (
          <span className="text-sm text-blue-400">
            {flag(activeTeam)} Path for <strong>{activeTeam}</strong>
          </span>
        )}
      </div>

      {activeTeam && reachProbs.length > 0 && (() => {
        const r = reachProbs.find((x) => x.team === activeTeam);
        if (!r) return null;
        const metrics = [
          ["Reach R32", r.reach_r32],
          ["Reach R16", r.reach_r16],
          ["Reach QF", r.reach_qf],
          ["Reach SF", r.reach_sf],
          ["Reach Final", r.reach_final],
          ["Win World Cup", r.reach_win],
        ] as const;
        return (
          <div className="mb-4 grid grid-cols-3 gap-2 md:grid-cols-6">
            {metrics.map(([label, val]) => (
              <div key={label} className="rounded-lg bg-slate-800/80 px-2 py-2 text-center">
                <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
                <div className="text-sm font-bold text-slate-100">{(val * 100).toFixed(0)}%</div>
              </div>
            ))}
          </div>
        );
      })()}

      {tooltip && (
        <p className="mb-3 rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-200 ring-1 ring-blue-500/40">
          {tooltip}
        </p>
      )}

      <div className="overflow-x-auto">
        <div className="mx-auto flex min-w-[1100px] items-start justify-center gap-3">
          <div className="flex gap-2.5">{leftSide}</div>

          {final && (
            <div className="mt-[120px] flex min-w-[220px] flex-col items-center px-2">
              <div className="mb-3 text-lg font-extrabold text-amber-400">
                🏆 FINAL
              </div>
              <MatchCard
                m={final}
                active={teamInMatch(final, activeTeam)}
                flag={flag}
                onHover={onHoverNode}
              />
              <p className="mt-3 text-center text-sm text-amber-200">
                {flag(final.winner)}{" "}
                <strong>{final.winner}</strong>
                <span className="mt-1 block text-xs text-slate-400">
                  {((data.champion_probs[final.winner] ?? 0) * 100).toFixed(1)}%
                  title
                </span>
              </p>
            </div>
          )}

          <div className="flex flex-row-reverse gap-2.5">{rightSide}</div>
        </div>
      </div>

      <p className="mt-3 text-center text-xs text-slate-500">
        Flag vs flag bracket — modal R32 draw + model knockout win probabilities.
      </p>
    </div>
  );
}
