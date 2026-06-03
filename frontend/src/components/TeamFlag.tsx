import "flag-icons/css/flag-icons.min.css";
import { teamFlagCode } from "../utils/teamFlags";

type Props = {
  team: string;
  size?: number;
  className?: string;
};

/** Local bundled flag (flag-icons). No Google/CDN requests. */
export default function TeamFlag({ team, size = 22, className = "" }: Props) {
  const code = teamFlagCode(team);
  if (!code) {
    return (
      <span
        className={`inline-flex shrink-0 items-center justify-center rounded bg-slate-600 text-[9px] font-bold text-slate-200 ${className}`}
        style={{ width: size, height: Math.round(size * 0.75) }}
        title={team}
      >
        ?
      </span>
    );
  }
  return (
    <span
      className={`fi fi-${code} fis inline-block shrink-0 rounded-sm shadow-sm ${className}`}
      style={{ width: size, height: Math.round(size * 0.75), fontSize: size }}
      title={team}
      aria-hidden
    />
  );
}
