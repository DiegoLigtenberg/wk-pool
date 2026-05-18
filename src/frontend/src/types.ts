export type PredictionStatus = "correct" | "wrong" | "pending";

export type MatchScore = {
  home: number;
  away: number;
};

export type AiPrediction = {
  pick: "1" | "2" | "3";
  confidence: number;
  explanation: string;
  status: PredictionStatus;
};

export type Match = {
  matchNumber: number;
  round: string;
  stage: "group" | "knockout";
  group: string | null;
  kickoffAt: string;
  location: string;
  homeTeam: string;
  awayTeam: string;
  status: "completed" | "upcoming";
  score: MatchScore | null;
  actualPick: "1" | "2" | "3" | null;
  aiPrediction: AiPrediction;
};

export type Standing = {
  team: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goalDifference: number;
  points: number;
};

export type Group = {
  name: string;
  standings: Standing[];
  matches: Match[];
};

export type TournamentView = {
  summary: {
    totalMatches: number;
    groupMatches: number;
    completed: number;
    upcoming: number;
    aiCorrect: number;
    aiWrong: number;
    aiPending: number;
    aiAccuracy: number;
  };
  nextMatch: Match | null;
  recentMatches: Match[];
  upcomingMatches: Match[];
  groups: Group[];
  knockoutMatches: Match[];
};

export type AppView = "matches" | "groups" | "knockout" | "crystal";
export type MatchStatusFilter = "all" | "completed" | "upcoming";
export type MatchPhaseFilter = "all" | "group" | "knockout";

export type SelectOption = {
  value: string;
  label: string;
};
