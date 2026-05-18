import { useEffect, useMemo, useState } from "react";
import { TeamInsightModal } from "./components/cards/TeamInsightModal";
import { TeamInsightProvider } from "./components/cards/TeamInsightContext";
import { CrystalBallView } from "./components/crystal/CrystalBallView";
import { GroupsView } from "./components/groups/GroupsView";
import { HeroNav } from "./components/layout/HeroNav";
import { MatchesView } from "./components/matches/MatchesView";
import { KnockoutView } from "./components/knockout/KnockoutView";
import { isTournamentView } from "./lib/contract";
import { allMatches } from "./lib/tournament";
import type { AppView, TournamentView } from "./types";

const API_TIMEOUT_MS = 10_000;
const apiBaseUrl = resolveApiBaseUrl();

export function App() {
  const [view, setView] = useState<AppView>("matches");
  const [tournament, setTournament] = useState<TournamentView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);

  useEffect(() => {
    if (!apiBaseUrl) {
      setError("VITE_API_BASE_URL ontbreekt. Zet deze build variable naar de publieke backend-URL.");
      return;
    }

    let active = true;
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    async function loadTournament() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/tournament`, {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Backend gaf status ${response.status}`);
        }
        const data = await response.json();
        if (!isTournamentView(data)) {
          throw new Error("Backend gaf een onverwacht tournament-formaat terug.");
        }
        if (active) {
          setTournament(data);
          setError(null);
        }
      } catch (unknownError) {
        if (active) {
          setError(errorMessage(unknownError));
        }
      }
    }

    void loadTournament();
    return () => {
      active = false;
      window.clearTimeout(timeoutId);
      controller.abort();
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
    <TeamInsightProvider insights={tournament.teamInsights} openTeam={setSelectedTeam}>
      <main className="app-shell">
        <HeroNav activeView={view} onChange={setView} />
        {view === "matches" ? <MatchesView matches={matches} summary={tournament.summary} /> : null}
        {view === "groups" ? <GroupsView tournament={tournament} /> : null}
        {view === "knockout" ? <KnockoutView knockoutMatches={tournament.knockoutMatches} /> : null}
        {view === "crystal" ? <CrystalBallView groups={tournament.groups} /> : null}
      </main>
      <TeamInsightModal insight={selectedTeam ? tournament.teamInsights[selectedTeam] ?? null : null} onClose={() => setSelectedTeam(null)} />
    </TeamInsightProvider>
  );
}

function resolveApiBaseUrl(): string | null {
  const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (configuredApiBaseUrl) {
    return normalizeApiBaseUrl(configuredApiBaseUrl);
  }

  return import.meta.env.DEV ? "http://127.0.0.1:8000" : null;
}

function normalizeApiBaseUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

function errorMessage(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "Backend reageerde niet op tijd.";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

