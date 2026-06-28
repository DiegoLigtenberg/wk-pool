import type { Match } from "../types";
import { displayTeamName, hasKnownTeams } from "./teams";

export function formatDateShort(value: string): string {
  return new Intl.DateTimeFormat("nl-NL", {
    day: "numeric",
    month: "short",
  }).format(new Date(value));
}

export function formatTime(value: string): string {
  return new Intl.DateTimeFormat("nl-NL", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function renderScore(match: Match): string {
  return match.score ? `${match.score.home} - ${match.score.away}` : "vs";
}

export function predictionLabel(match: Match): string {
  if (!hasKnownTeams(match)) {
    return "Onbekend";
  }

  if (match.aiPrediction.pick === "1") {
    return `${displayTeamName(match.homeTeam)} wint`;
  }
  if (match.aiPrediction.pick === "2") {
    return `${displayTeamName(match.awayTeam)} wint`;
  }
  return "Gelijkspel";
}

export function roundLabelNl(round: string): string {
  const labels: Record<string, string> = {
    "Round of 32": "Zestiende finale",
    "Round of 16": "Achtste finale",
    "Quarter Finals": "Kwartfinale",
    "Semi Finals": "Halve finale",
    Finals: "Finale + troostfinale",
  };

  return labels[round] ?? round;
}

export function formatKnockoutDateShort(value: string): string {
  return new Intl.DateTimeFormat("nl-NL", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function phaseLabel(match: Match): string {
  if (match.stage === "group") {
    return `Poule ${match.group ?? "-"}`;
  }
  return roundLabelNl(match.round);
}
