import type { Match, TeamInsight, TournamentView } from "../types";

const mexicoInsight: TeamInsight = {
  team: "Mexico",
  tier: "Betrouwbare outsider",
  style: "intens en thuisregio-gedreven",
  strengths: ["publieksenergie", "ervaring"],
  risks: ["druk op de ploeg"],
  niche: ["openingswedstrijd kan veel invloed hebben"],
  summary: "Mexico krijgt extra waarde door thuisregio en publiek.",
};

const southAfricaInsight: TeamInsight = {
  team: "South Africa",
  tier: "Outsider",
  style: "energiek en opportunistisch",
  strengths: ["wedstrijdenergie", "counters"],
  risks: ["controle"],
  niche: ["kan profiteren als de tegenstander onder druk staat"],
  summary: "South Africa kan via energie fases kantelen.",
};

export const completedMatch: Match = {
  matchNumber: 1,
  round: "1",
  stage: "group",
  group: "A",
  kickoffAt: "2026-06-11T19:00:00Z",
  location: "Mexico City",
  homeTeam: "Mexico",
  awayTeam: "South Africa",
  status: "completed",
  score: { home: 2, away: 0 },
  actualPick: "1",
  aiPrediction: {
    pick: "1",
    confidence: 58,
    explanation: "Mexico krijgt het voordeel door thuisregio en openingsenergie.",
    status: "correct",
    themes: ["thuisregio en publiek", "groepscontext Poule A"],
    homeWinProbability: 58,
    drawProbability: 25,
    awayWinProbability: 17,
  },
};

export const upcomingMatch: Match = {
  matchNumber: 73,
  round: "Round of 32",
  stage: "knockout",
  group: null,
  kickoffAt: "2026-06-28T19:00:00Z",
  location: "Los Angeles",
  homeTeam: "1A",
  awayTeam: "2B",
  status: "upcoming",
  score: null,
  actualPick: null,
  aiPrediction: {
    pick: "3",
    confidence: 0,
    explanation: "De AI wacht met inhoudelijke voorspelling tot beide landen bekend zijn.",
    status: "pending",
    themes: ["Teams nog onbekend"],
    homeWinProbability: null,
    drawProbability: null,
    awayWinProbability: null,
  },
};

export function tournamentFixture(overrides: Partial<TournamentView> = {}): TournamentView {
  return {
    summary: {
      totalMatches: 2,
      groupMatches: 1,
      completed: 1,
      upcoming: 1,
      aiCorrect: 1,
      aiWrong: 0,
      aiPending: 0,
      aiAccuracy: 100,
    },
    nextMatch: upcomingMatch,
    recentMatches: [completedMatch],
    upcomingMatches: [upcomingMatch],
    teamInsights: {
      Mexico: mexicoInsight,
      "South Africa": southAfricaInsight,
    },
    groups: [
      {
        name: "A",
        standings: [
          {
            team: "Mexico",
            played: 1,
            wins: 1,
            draws: 0,
            losses: 0,
            goalsFor: 2,
            goalsAgainst: 0,
            goalDifference: 2,
            points: 3,
          },
          {
            team: "South Africa",
            played: 1,
            wins: 0,
            draws: 0,
            losses: 1,
            goalsFor: 0,
            goalsAgainst: 2,
            goalDifference: -2,
            points: 0,
          },
        ],
        matches: [completedMatch],
      },
    ],
    knockoutMatches: [upcomingMatch],
    ...overrides,
  };
}
