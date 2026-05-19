export type PredictionStatus = "correct" | "wrong" | "pending";

export type MatchScore = {
  home: number;
  away: number;
};

export type PredictionFactor = {
  id: string;
  delta: number;
  label: string;
  reason: string;
  scope: "match" | "team";
};

export type PredictionScoreSide = {
  team: string;
  powerScore: number;
  contextDelta: number;
  effectiveScore: number;
  factors: PredictionFactor[];
};

export type PredictionStep = {
  title: string;
  body: string;
};

export type PredictionInsight = {
  scoreSummary: string;
  verdict: string;
  /** Nieuwere backend; ontbreekt bij verouderde server tot herstart. */
  narrative?: string;
  steps?: PredictionStep[];
  tags: string[];
  diff: number;
  winnerSide?: "home" | "away";
  home: PredictionScoreSide;
  away: PredictionScoreSide;
};

export type AiPrediction = {
  pick: "1" | "2" | "3";
  confidence: number;
  explanation: string;
  status: PredictionStatus;
  insight?: PredictionInsight;
  homeWinProbability: number | null;
  drawProbability: number | null;
  awayWinProbability: number | null;
};

export type TeamInsight = {
  team: string;
  tier: string;
  style: string;
  powerScore?: number;
  strengths: string[];
  risks: string[];
  group?: string;
  opponents?: string[];
  groupContext?: string[];
  distinctiveSpark?: string | null;
  niche?: string[];
  summary: string;
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
  goalsFor: number;
  goalsAgainst: number;
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
  teamInsights: Record<string, TeamInsight>;
  groups: Group[];
  knockoutMatches: Match[];
};

export type AppView = "matches" | "groups" | "knockout" | "crystal";
export type MatchStatusFilter = "all" | "completed" | "upcoming";
export type MatchPhaseFilter = "all" | "knockout" | `group:${string}`;

export type SelectOption = {
  value: string;
  label: string;
};
