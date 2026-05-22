import { useEffect, useMemo, useState } from "react";
import { TeamInsightModal } from "./components/cards/TeamInsightModal";
import { TeamInsightProvider } from "./components/cards/TeamInsightContext";
import { CrystalBallView } from "./components/crystal/CrystalBallView";
import { GroupsView } from "./components/groups/GroupsView";
import { HeroNav } from "./components/layout/HeroNav";
import { MatchesView } from "./components/matches/MatchesView";
import { KnockoutView } from "./components/knockout/KnockoutView";
import { describeUnexpectedTournamentPayload, isTournamentView } from "./lib/contract";
import { allMatches } from "./lib/tournament";
import type { AppView, TournamentView } from "./types";

const API_TIMEOUT_MS = 30_000;
const apiBaseUrl = resolveApiBaseUrl();
const tournamentApiUrl =
  apiBaseUrl === null ? null : apiBaseUrl ? `${apiBaseUrl}/api/tournament` : "/api/tournament";

export function App() {
  const [view, setView] = useState<AppView>("matches");
  const [tournament, setTournament] = useState<TournamentView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);

  useEffect(() => {
    if (apiBaseUrl === null) {
      setError("VITE_API_BASE_URL ontbreekt. Zet deze build variable naar de publieke backend-URL.");
      return;
    }

    let active = true;
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    async function loadTournament() {
      try {
        const response = await fetch(tournamentApiUrl!, {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Backend gaf status ${response.status} (${tournamentApiUrl})`);
        }
        const data: unknown = await response.json();
        if (!isTournamentView(data)) {
          throw new Error(describeUnexpectedTournamentPayload(data, tournamentApiUrl!));
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
        <h1>{errorHeadline(error)}</h1>
        <p>
          Start de backend met <code>poetry run wk-pool-backend</code> vanuit <code>src/backend</code>.
          Zorg dat er maar één proces op poort <code>8000</code> luistert.
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
        {view === "crystal" ? <CrystalBallView crystalBall={tournament.crystalBall} /> : null}
      </main>
      <TeamInsightModal insight={selectedTeam ? tournament.teamInsights[selectedTeam] ?? null : null} onClose={() => setSelectedTeam(null)} />
    </TeamInsightProvider>
  );
}

function resolveApiBaseUrl(): string | null {
  // Local dev always uses the Vite proxy (same origin) → 127.0.0.1:8000.
  // Ignores VITE_API_BASE_URL so a stale Railway URL in your shell cannot break local dev.
  if (import.meta.env.DEV) {
    return "";
  }

  const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (configuredApiBaseUrl) {
    return normalizeApiBaseUrl(configuredApiBaseUrl);
  }

  return null;
}

function normalizeApiBaseUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

function errorHeadline(message: string): string {
  if (message === "Backend reageerde niet op tijd.") {
    return "Backend reageerde te traag.";
  }
  if (message.startsWith("Backend gaf status")) {
    return "Backend gaf een fout.";
  }
  if (message.includes("Ongeldige velden:") || message.includes("Onbekend formaat") || message.includes("/health")) {
    return "Backend-data komt niet overeen.";
  }
  if (message.includes("VITE_API_BASE_URL")) {
    return "Frontend-configuratie ontbreekt.";
  }
  return "Backend is niet bereikbaar.";
}

function errorMessage(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "Backend reageerde niet op tijd.";
  }
  if (error instanceof TypeError) {
    return "Kon geen verbinding maken met de backend (controleer of die draait en of poort 8000 vrij is).";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

