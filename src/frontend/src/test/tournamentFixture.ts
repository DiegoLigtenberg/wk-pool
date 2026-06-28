import type { Match, TeamInsight, TournamentView } from "../types";

const mexicoInsight: TeamInsight = {
  team: "Mexico",
  tier: "Subtopper",
  style: "intens en thuisregio-gedreven",
  strengths: ["publieksenergie", "ervaring"],
  risks: ["druk op de ploeg"],
  niche: ["openingswedstrijd kan veel invloed hebben"],
  summary: "Mexico krijgt extra waarde door thuisregio en publiek.",
};

const southAfricaInsight: TeamInsight = {
  team: "Zuid-Afrika",
  tier: "Kanshebber",
  style: "energiek en opportunistisch",
  powerScore: 66,
  strengths: ["wedstrijdenergie", "counters"],
  risks: ["controle"],
  group: "A",
  opponents: ["Mexico", "Tsjechië", "Zuid-Korea"],
  groupContext: [
    "Wedstrijd 1: thuis tegen Tsjechië (Guadalajara Stadium)",
    "Wedstrijd 2: uit tegen Mexico (Guadalajara Stadium)",
  ],
  summary: "Zuid-Afrika kan via energie fases kantelen.",
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
    explanation:
      "In groepsronde 1 ligt Mexico voor (82, 65 effectief). Belangrijkste signalen uit research: Omschakeling/transities passen tegen compact Zuid-Afrika.",
    status: "correct",
    insight: {
      scoreSummary:
        "Mexico 82 – Zuid-Afrika 65 (17 punten verschil in wedstrijdscore). Mexico heeft in deze analyse net iets meer kansen dan Zuid-Afrika.",
      leadSummary:
        "Mexico speelt thuis als co-host. Hun spel past bij de compacte verdediging van Zuid-Afrika.",
      verdict: "De AI voorspelt dat Mexico wint.",
      pickLogicNote: "",
      narrative:
        "Dit is berekend met ons AI-model. Mexico staat hoger (82 tegen 65 voor Zuid-Afrika).\n\nDat ondersteunt de voorspelling: Mexico kan snel omschakelen tegen het lage blok van Zuid-Afrika.",
      steps: [
        {
          title: "Hoe dit werkt",
          body: "Dit rekent ons AI-model uit in één getal per team: basissterkte plus aanpassingen uit Mexico–Zuid-Afrika en uit de hele groepsfase. In de kaarten hieronder zie je het totaal (wedstrijdscore) en welke onderdelen meetellen (+ en −).",
        },
        {
          title: "Belangrijk in dit duel",
          body: "Mexico speelt thuis als co-host. Hun spel past bij de compacte verdediging van Zuid-Afrika, terwijl Zuid-Afrika weinig doelpuntenkansen haalt tegen Giménez en Jiménez achterin.",
        },
      ],
      tags: ["Mexico: Tactiek +1", "Mexico: Co-host +3"],
      diff: 17,
      winnerSide: "home",
      home: {
        team: "Mexico",
        powerScore: 77,
        contextDelta: 5,
        researchDelta: 2,
        hostDelta: 3,
        travelDelta: 0,
        effectiveScore: 82,
        factors: [
          {
            id: "style_matchup",
            delta: 1,
            label: "Tactiek",
            reason: "Omschakeling/transities passen tegen compact Zuid-Afrika",
            scope: "match",
          },
          {
            id: "host_region",
            delta: 3,
            label: "Co-host",
            reason: "Co-host: thuisregio en publiek",
            scope: "team",
          },
        ],
      },
      away: {
        team: "Zuid-Afrika",
        powerScore: 66,
        contextDelta: -1,
        effectiveScore: 65,
        factors: [
          {
            id: "distinctive_spark",
            delta: -1,
            label: "Opvallend",
            reason: "Opener op hoogte vs co-host Mexico",
            scope: "team",
          },
        ],
      },
    },
    homeWinProbability: 58,
    drawProbability: 25,
    awayWinProbability: 17,
    suggestedScore: {
      home: 2,
      away: 0,
      reason: "Overtuigende winst voor thuis; 2-0 in de poule.",
    },
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
      Mexico: { ...mexicoInsight, team: "Mexico" },
      "Zuid-Afrika": { ...southAfricaInsight, team: "Zuid-Afrika" },
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
            team: "Zuid-Afrika",
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
        predictedWinner: "Mexico",
        winnerPredictionStatus: "correct",
      },
    ],
    knockoutMatches: [upcomingMatch],
    crystalBall: {
      groupWinners: [{ group: "A", team: "Mexico", status: "correct" }],
      projectedGroups: [
        {
          name: "A",
          winner: "Mexico",
          standings: [
            {
              team: "Mexico",
              played: 1,
              wins: 1,
              draws: 0,
              losses: 0,
              goalsFor: 1,
              goalsAgainst: 0,
              goalDifference: 1,
              points: 3,
            },
            {
              team: "Zuid-Afrika",
              played: 1,
              wins: 0,
              draws: 0,
              losses: 1,
              goalsFor: 0,
              goalsAgainst: 1,
              goalDifference: -1,
              points: 0,
            },
          ],
        },
      ],
      bonusQuestions: [
        {
          id: "yellow_cards_total",
          label: "Gele kaarten",
          value: "368",
          helper: "Test helper",
        },
        {
          id: "direct_red_cards",
          label: "Direct rood",
          value: "7",
          helper: "Test helper",
        },
        {
          id: "champion",
          label: "Wereldkampioen",
          value: "Frankrijk",
          helper: "Test helper",
        },
        {
          id: "top_scorer",
          label: "Topscorer",
          value: "Kylian Mbappé",
          helper: "Test helper",
        },
      ],
      sources: ["test"],
      contextAsOf: "2026-05-19",
      liveStats: {
        source: "espn",
        updatedAt: null,
        completedMatches: 1,
        totalMatches: 104,
        yellowCards: 3,
        directRedCards: 0,
        topScorer: null,
      },
    },
    ...overrides,
  };
}
