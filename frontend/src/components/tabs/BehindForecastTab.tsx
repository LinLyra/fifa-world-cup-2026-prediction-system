import Section from "../Section";
import { SIMULATIONS } from "../../utils/format";

export default function BehindForecastTab() {
  return (
    <Section title="📐 Behind the Forecast" tagline="How does the model work?">
      <div className="method-box">
        <h3>49,000+ International Matches</h3>
        <p>
          The engine is trained on more than 49,000 historical international football matches spanning over a century
          of competition. This is the foundation for every team rating and probability on the dashboard.
        </p>

        <h3>Team Strength Modelling</h3>
        <p>
          Each national team is represented through a multi-layer strength profile built from historical performance,
          attacking output, defensive resilience, squad value, and market signals.
        </p>

        <h3>Probabilistic Match Forecasting</h3>
        <p>
          Match outcomes are generated with Poisson-based scoreline modelling and Dixon–Coles low-score correction,
          producing realistic expected goals, score distributions, and win/draw/loss probabilities.
        </p>

        <h3>Tournament Simulation</h3>
        <p>
          We run {SIMULATIONS.toLocaleString()} Monte Carlo simulations of the full FIFA World Cup 2026 structure, from
          the group stage to the knockout rounds and final, to estimate advancement and title probabilities.
        </p>

        <h3>Pre-Match Intelligence</h3>
        <p>
          Before kickoff, the model can incorporate squad availability, tactical profile, betting market movement, and
          competitive context to refine match expectations.
        </p>

        <h3>Squad Availability Intelligence</h3>
        <p>
          Player absences, suspensions, and squad disruptions are tracked and translated into team-level adjustments,
          helping the model reflect real-world availability without exposing private pipeline details.
        </p>
      </div>
    </Section>
  );
}
