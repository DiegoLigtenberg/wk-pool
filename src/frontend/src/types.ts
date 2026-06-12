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
  /** Onderdelen van contextDelta (nieuwere backend). */
  researchDelta?: number;
  hostDelta?: number;
  travelDelta?: number;
  effectiveScore: number;
  factors: PredictionFactor[];
};

export type PredictionStep = {
  title: string;
  body: string;
};

export type PickStep = {
  title: string;
  body: string;
  delta?: number;
  kind?: string;
  runningDiff?: number;
  pick?: "1" | "2" | "3";
};

export type PoolAdjustment = {
  id: string;
  kind: string;
  label: string;
  delta: number;
  reason: string;
};

export type SuggestedScore = {
  home: number;
  away: number;
  reason: string;
};

export type PredictionInsight = {
  scoreSummary: string;
  /** Korte uitleg zonder wedstrijdscore-cijfers (zichtbaar vóór uitklap). */
  leadSummary?: string;
  verdict: string;
  /** Nieuwere backend; ontbreekt bij verouderde server tot herstart. */
  narrative?: string;
  steps?: PredictionStep[];
  tags: string[];
  /** Pool-score na bijsturing (pick/kansen). */
  diff: number;
  /** Alleen research-context, vóór pool-bijsturing. */
  baseDiff?: number;
  pickSteps?: PickStep[];
  poolAdjustments?: PoolAdjustment[];
  /** Leeg bij nieuwe payloads; pick-uitleg staat achteraan in `scoreSummary` onder research-details. */
  pickLogicNote?: string;
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
  /** Voorgestelde uitslag bij pool-pick (1-X-2). */
  suggestedScore?: SuggestedScore;
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
  predictedWinner: string;
  winnerPredictionStatus: PredictionStatus;
};

export type CrystalBallGroupWinner = {
  group: string;
  team: string;
  status: PredictionStatus;
};

export type ProjectedGroup = {
  name: string;
  winner: string | null;
  standings: Standing[];
};

export type CrystalBallBonusQuestion = {
  id: string;
  label: string;
  value: string;
  helper: string;
  rationale?: string;
};

export type CrystalBallTopScorer = {
  name: string;
  goals: number;
  team: string;
};

export type CrystalBallLiveStats = {
  source: "espn" | "api-football";
  updatedAt: string | null;
  completedMatches: number;
  totalMatches: number;
  yellowCards: number;
  directRedCards: number;
  topScorer: CrystalBallTopScorer | null;
};

export type CrystalBallView = {
  groupWinners: CrystalBallGroupWinner[];
  projectedGroups: ProjectedGroup[];
  bonusQuestions: CrystalBallBonusQuestion[];
  sources: string[];
  contextAsOf: string;
  liveStats: CrystalBallLiveStats;
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
  crystalBall: CrystalBallView;
};

export type AppView = "matches" | "groups" | "knockout" | "crystal";
export type MatchStatusFilter = "all" | "completed" | "upcoming";
export type MatchPhaseFilter = "all" | "knockout" | `group:${string}`;

export type SelectOption = {
  value: string;
  label: string;
};
