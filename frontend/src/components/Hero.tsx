import type { Meta } from "../types";
import { SIMULATIONS } from "../utils/format";

type Props = { meta: Meta };

export default function Hero({ meta }: Props) {
  const metrics = [
    ["Simulations", meta.simulations.toLocaleString()],
    ["Historical Matches", meta.historical_matches],
    ["Teams Modeled", String(meta.team_count)],
    ["Engine", meta.engine],
  ] as const;

  return (
    <div className="hero-banner mb-6">
      <div className="hero-head">
        <h1>⚽ FIFA World Cup 2026 Forecast Engine</h1>
        <span className="hero-byline">
          by: <span className="hero-signature">LLyra</span>
        </span>
      </div>
      <p>
        Prediction Engine · Simulation Engine · Intelligence Layer — built on{" "}
        {meta.historical_matches} international matches and {SIMULATIONS.toLocaleString()}{" "}
        full-tournament Monte Carlo simulations from group stage to final.
      </p>
      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
        {metrics.map(([label, value]) => (
          <div key={label} className="metric-card">
            <div className="label">{label}</div>
            <div className="value">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
