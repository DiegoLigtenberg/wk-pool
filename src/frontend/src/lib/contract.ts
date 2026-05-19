import type { TournamentView } from "../types";

/** Runtime shape check for `/api/tournament`; keep aligned with `tests/test_webapp.py` (`is_tournament_view`). */
const PICKS = new Set(["1", "2", "3"]);
const PREDICTION_STATUSES = new Set(["correct", "wrong", "pending"]);
const MATCH_STATUSES = new Set(["completed", "upcoming"]);
const MATCH_STAGES = new Set(["group", "knockout"]);

export function isTournamentView(value: unknown): value is TournamentView {
  return getTournamentValidationErrors(value).length === 0;
}

/** Human-readable paths for dev error UI; keep in sync with validators below. */
export function getTournamentValidationErrors(value: unknown, limit = 8): string[] {
  const errors: string[] = [];
  const push = (path: string, ok: boolean) => {
    if (!ok && errors.length < limit) {
      errors.push(path);
    }
  };

  if (!isRecord(value)) {
    return ["root: expected object"];
  }

  push("summary", isSummary(value.summary));

  if (value.nextMatch !== null) {
    push("nextMatch", isMatch(value.nextMatch));
  }

  if (!Array.isArray(value.recentMatches)) {
    push("recentMatches", false);
  } else {
    for (const match of value.recentMatches) {
      if (!isMatch(match) && isRecord(match)) {
        push(`recentMatches[${match.matchNumber}]`, false);
        break;
      }
    }
  }

  if (!Array.isArray(value.upcomingMatches)) {
    push("upcomingMatches", false);
  } else {
    for (const match of value.upcomingMatches) {
      if (!isMatch(match) && isRecord(match)) {
        push(`upcomingMatches[${match.matchNumber}]`, false);
        break;
      }
    }
  }

  if (!isTeamInsights(value.teamInsights)) {
    push("teamInsights", false);
  }

  if (!Array.isArray(value.groups)) {
    push("groups", false);
  } else {
    for (const group of value.groups) {
      if (!isGroup(group) && isRecord(group)) {
        push(`groups[${group.name ?? "?"}]`, false);
        break;
      }
    }
  }

  if (!Array.isArray(value.knockoutMatches)) {
    push("knockoutMatches", false);
  } else {
    for (const match of value.knockoutMatches) {
      if (!isMatch(match) && isRecord(match)) {
        push(`knockoutMatches[${match.matchNumber}]`, false);
        break;
      }
    }
  }

  return errors;
}

export function describeUnexpectedTournamentPayload(value: unknown, apiUrl: string): string {
  if (isRecord(value) && value.status === "ok" && value.service === "wk-pool-backend") {
    return `Antwoord lijkt op /health, niet op toernooidata. API-basis: ${apiUrl}`;
  }
  if (isRecord(value) && typeof value.error === "string") {
    return `Backend: ${value.error} (${apiUrl})`;
  }

  const fieldErrors = getTournamentValidationErrors(value);
  if (fieldErrors.length > 0) {
    return `Ongeldige velden: ${fieldErrors.join(", ")} (${apiUrl})`;
  }

  return `Onbekend formaat (${apiUrl})`;
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
    typeof value.summary === "string" &&
    (value.niche == null || isStringArray(value.niche)) &&
    (value.opponents == null || isStringArray(value.opponents)) &&
    (value.group === undefined || typeof value.group === "string") &&
    (value.powerScore === undefined || isNumber(value.powerScore)) &&
    (value.groupContext == null || isStringArray(value.groupContext)) &&
    (value.distinctiveSpark == null || typeof value.distinctiveSpark === "string")
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
    (value.confidence === 0 ? value.insight == null : isPredictionInsight(value.insight)) &&
    (value.homeWinProbability === null || isNumber(value.homeWinProbability)) &&
    (value.drawProbability === null || isNumber(value.drawProbability)) &&
    (value.awayWinProbability === null || isNumber(value.awayWinProbability))
  );
}

function isPredictionInsight(value: unknown): boolean {
  if (!isRecord(value)) {
    return false;
  }
  const narrativeOk = value.narrative == null || typeof value.narrative === "string";
  const stepsOk =
    value.steps == null || (Array.isArray(value.steps) && value.steps.every(isPredictionStep));
  return (
    typeof value.scoreSummary === "string" &&
    typeof value.verdict === "string" &&
    narrativeOk &&
    stepsOk &&
    isStringArray(value.tags) &&
    isNumber(value.diff) &&
    isPredictionScoreSide(value.home) &&
    isPredictionScoreSide(value.away)
  );
}

function isPredictionStep(value: unknown): boolean {
  return (
    isRecord(value) &&
    typeof value.title === "string" &&
    typeof value.body === "string"
  );
}

function isPredictionScoreSide(value: unknown): boolean {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.team === "string" &&
    isNumber(value.powerScore) &&
    isNumber(value.contextDelta) &&
    isNumber(value.effectiveScore) &&
    Array.isArray(value.factors) &&
    value.factors.every(isPredictionFactor)
  );
}

function isPredictionFactor(value: unknown): boolean {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.id === "string" &&
    isNumber(value.delta) &&
    typeof value.label === "string" &&
    typeof value.reason === "string" &&
    (value.scope === "match" || value.scope === "team")
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
