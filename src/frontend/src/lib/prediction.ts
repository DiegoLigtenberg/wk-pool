import { type Match } from "../types";

export function formatSuggestedScore(match: Match): string | null {
  const suggested = match.aiPrediction.suggestedScore;
  if (!suggested) {
    return null;
  }
  return `${suggested.home} - ${suggested.away}`;
}

export function pickCodeLabel(pick: Match["aiPrediction"]["pick"]): string {
  if (pick === "1") {
    return "1";
  }
  if (pick === "2") {
    return "2";
  }
  return "3";
}

export function pickOutcomeLabel(match: Match): string {
  const pick = match.aiPrediction.pick;
  if (pick === "1") {
    return "Thuis wint";
  }
  if (pick === "2") {
    return "Uit wint";
  }
  return "Gelijk";
}
