import { useEffect, useMemo, useState } from "react";
import { CrystalBallView } from "./components/crystal/CrystalBallView";
import { GroupsView } from "./components/groups/GroupsView";
import { HeroNav } from "./components/layout/HeroNav";
import { MatchesView } from "./components/matches/MatchesView";
import { KnockoutView } from "./components/knockout/KnockoutView";
import { allMatches } from "./lib/tournament";
import type { AppView, TournamentView } from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function App() {
  const [view, setView] = useState<AppView>("matches");
  const [tournament, setTournament] = useState<TournamentView | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadTournament() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/tournament`);
        if (!response.ok) {
          throw new Error(`Backend gaf status ${response.status}`);
        }
        const data = (await response.json()) as TournamentView;
        if (active) {
          setTournament(data);
        }
      } catch (unknownError) {
        if (active) {
          setError(String(unknownError));
        }
      }
    }

    void loadTournament();
    return () => {
      active = false;
    };
  }, []);

  const matches = useMemo(() => (tournament ? allMatches(tournament) : []), [tournament]);

  if (error) {
    return (
      <main className="app-shell error-state">
        <p className="eyebrow">WK Pool</p>
        <h1>Backend draait niet.</h1>
        <p>
          Start de backend met <code>poetry run wk-pool-backend</code> vanuit <code>src/backend</code>.
        </p>
        <p className="muted">{error}</p>
      </main>
    );
  }

  if (!tournament) {
    return (
      <main className="app-shell">
        <p className="loading">WK Pool laden...</p>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <HeroNav activeView={view} onChange={setView} />
      {view === "matches" ? <MatchesView matches={matches} summary={tournament.summary} /> : null}
      {view === "groups" ? <GroupsView tournament={tournament} /> : null}
      {view === "knockout" ? <KnockoutView knockoutMatches={tournament.knockoutMatches} /> : null}
      {view === "crystal" ? <CrystalBallView groups={tournament.groups} /> : null}
    </main>
  );
}
