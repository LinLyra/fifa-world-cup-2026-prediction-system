import { track } from "@vercel/analytics";
import { useState } from "react";
import Hero from "./components/Hero";
import BehindForecastTab from "./components/tabs/BehindForecastTab";
import BracketTab from "./components/tabs/BracketTab";
import ChampionTab from "./components/tabs/ChampionTab";
import GroupsTab from "./components/tabs/GroupsTab";
import MatchupsTab from "./components/tabs/MatchupsTab";
import PathDifficultyTab from "./components/tabs/PathDifficultyTab";
import PowerRankingsTab from "./components/tabs/PowerRankingsTab";
import { useDashboardData } from "./hooks/useDashboardData";
import { SIMULATIONS } from "./utils/format";
import { wcTeamSet } from "./utils/wcTeams";

const TABS = [
  { id: "champion", label: "🏆 Champion" },
  { id: "groups", label: "📊 Groups" },
  { id: "bracket", label: "🌳 Bracket" },
  { id: "path", label: "🛤️ Path Difficulty" },
  { id: "matchups", label: "⚔️ Matchups" },
  { id: "power", label: "💪 Power Rankings" },
  { id: "behind", label: "📐 Behind the Forecast" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const { data, error, loading } = useDashboardData();
  const [tab, setTab] = useState<TabId>("champion");

  if (loading) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-16 text-center text-[#555]">
        Loading forecast data…
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">{error}</div>
      </main>
    );
  }

  const teams = wcTeamSet(data.fixtures, data.groups, data.champions);

  const selectTab = (id: TabId) => {
    setTab(id);
    track("dashboard_tab", { tab: id });
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-[#F7F9F8] to-[#EEF2EF] px-4 py-6">
      <div className="mx-auto max-w-7xl">
        <Hero meta={data.meta} />

        <div className="mb-6 flex flex-wrap gap-1 border-b border-[#E0E8E3]">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => selectTab(t.id)}
              className={`rounded-t-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                tab === t.id
                  ? "border border-b-0 border-[#E0E8E3] bg-white text-[#1B5E20] font-bold"
                  : "text-[#111] hover:bg-white/60"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="rounded-b-xl rounded-tr-xl border border-[#E0E8E3] bg-white/50 p-4 md:p-6">
          {tab === "champion" && <ChampionTab champions={data.champions} />}
          {tab === "groups" && <GroupsTab groups={data.groups} />}
          {tab === "bracket" && (
            <BracketTab
              bracket={data.bracket}
              reachProbs={data.reachProbs}
              groups={data.groups}
              fixtures={data.fixtures}
            />
          )}
          {tab === "path" && (
            <PathDifficultyTab pathDifficulty={data.pathDifficulty} champions={data.champions} />
          )}
          {tab === "matchups" && (
            <MatchupsTab
              matchMatrix={data.matchMatrix}
              finalIntel={data.finalIntel}
              fixtures={data.fixtures}
              intelligence={data.intelligence}
              teams={teams}
            />
          )}
          {tab === "power" && <PowerRankingsTab intelligence={data.intelligence} />}
          {tab === "behind" && <BehindForecastTab />}
        </div>

        <footer className="footer-note">
          FIFA World Cup 2026 Forecast Engine — Prediction · Simulation · Intelligence
          <br />
          <span className="text-sm text-[#555]">
            V2 Pre-Match Forecast · {SIMULATIONS.toLocaleString()} tournament simulations
          </span>
        </footer>
      </div>
    </main>
  );
}
