import type { TournamentView } from "../types";

const PICKS = new Set(["1", "2", "3"]);
const PREDICTION_STATUSES = new Set(["correct", "wrong", "pending"]);
const MATCH_STATUSES = new Set(["completed", "upcoming"]);
const MATCH_STAGES = new Set(["group", "knockout"]);

export function isTournamentView(value: unknown): value is TournamentView {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isSummary(value.summary) &&
    (value.nextMatch === null || isMatch(value.nextMatch)) &&
    Array.isArray(value.recentMatches) &&
    value.recentMatches.every(isMatch) &&
    Array.isArray(value.upcomingMatches) &&
    value.upcomingMatches.every(isMatch) &&
    isTeamInsights(value.teamInsights) &&
    Array.isArray(value.groups) &&
    value.groups.every(isGroup) &&
    Array.isArray(value.knockoutMatches) &&
    value.knockoutMatches.every(isMatch)
  );
}

function isSummary(value: unknown): boolean {
  return (
    isRecord(value) &&
    isNumber(value.totalMatches) &&
    isNumber(value.groupMatches) &&
    isNumber(value.completed) &&
    isNumber(value.upcoming) &&
    isNumber(value.aiCorrect) &&
    isNumber(value.aiWrong) &&
    isNumber(value.aiPending) &&
    isNumber(value.aiAccuracy)
  );
}

function isTeamInsights(value: unknown): boolean {
  return isRecord(value) && Object.values(value).every(isTeamInsight);
}

function isTeamInsight(value: unknown): boolean {
  return (
    isRecord(value) &&
    typeof value.team === "string" &&
    typeof value.tier === "string" &&
    typeof value.style === "string" &&
    isStringArray(value.strengths) &&
    isStringArray(value.risks) &&
    isStringArray(value.niche) &&
    typeof value.summary === "string"
  );
}

function isGroup(value: unknown): boolean {
  return (
    isRecord(value) &&
    typeof value.name === "string" &&
    Array.isArray(value.standings) &&
    value.standings.every(isStanding) &&
    Array.isArray(value.matches) &&
    value.matches.every(isMatch)
  );
}

function isStanding(value: unknown): boolean {
  return (
    isRecord(value) &&
    typeof value.team === "string" &&
    isNumber(value.played) &&
    isNumber(value.wins) &&
    isNumber(value.draws) &&
    isNumber(value.losses) &&
    isNumber(value.goalsFor) &&
    isNumber(value.goalsAgainst) &&
    isNumber(value.goalDifference) &&
    isNumber(value.points)
  );
}

function isMatch(value: unknown): boolean {
  return (
    isRecord(value) &&
    isNumber(value.matchNumber) &&
    typeof value.round === "string" &&
    MATCH_STAGES.has(value.stage as string) &&
    (typeof value.group === "string" || value.group === null) &&
    typeof value.kickoffAt === "string" &&
    typeof value.location === "string" &&
    typeof value.homeTeam === "string" &&
    typeof value.awayTeam === "string" &&
    MATCH_STATUSES.has(value.status as string) &&
    (value.score === null || isScore(value.score)) &&
    (value.actualPick === null || PICKS.has(value.actualPick as string)) &&
    isAiPrediction(value.aiPrediction)
  );
}

function isAiPrediction(value: unknown): boolean {
  return (
    isRecord(value) &&
    PICKS.has(value.pick as string) &&
    isNumber(value.confidence) &&
    typeof value.explanation === "string" &&
    PREDICTION_STATUSES.has(value.status as string) &&
    isStringArray(value.themes) &&
    (value.homeWinProbability === null || isNumber(value.homeWinProbability)) &&
    (value.drawProbability === null || isNumber(value.drawProbability)) &&
    (value.awayWinProbability === null || isNumber(value.awayWinProbability))
  );
}

function isScore(value: unknown): boolean {
  return isRecord(value) && isNumber(value.home) && isNumber(value.away);
}

function isStringArray(value: unknown): boolean {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
