import type { Match } from "../../types";
import { formatSuggestedScore, pickCodeLabel, pickOutcomeLabel } from "../../lib/prediction";
import { hasKnownTeams } from "../../lib/teams";
import "./PredictedOutcome.css";

type PredictedOutcomeProps = {
  match: Match;
  variant?: "inline" | "panel" | "compact";
};

export function PredictedOutcome({ match, variant = "inline" }: PredictedOutcomeProps) {
  if (!hasKnownTeams(match)) {
    return null;
  }

  const score = formatSuggestedScore(match);
  if (!score) {
    return null;
  }

  const pick = match.aiPrediction.pick;
  const reason = match.aiPrediction.suggestedScore?.reason;

  if (variant === "panel") {
    return (
      <div className="prediction-suggested-score">
        <span className="prediction-suggested-score__label">Voorspelde uitslag (90 min)</span>
        <strong className="prediction-suggested-score__line">{score}</strong>
        <p className="prediction-suggested-score__meta">
          Toto <span className="prediction-suggested-score__pick">{pickCodeLabel(pick)}</span>
          {" · "}
          {pickOutcomeLabel(match)}
          {match.aiPrediction.confidence > 0 ? ` · ${match.aiPrediction.confidence}%` : null}
        </p>
        {reason ? <p className="prediction-suggested-score__reason">{reason}</p> : null}
      </div>
    );
  }

  if (variant === "compact") {
    return (
      <span className="predicted-outcome predicted-outcome--compact" title={reason ?? undefined}>
        <span className="predicted-outcome__score">{score}</span>
        <span className="predicted-outcome__pick">{pickCodeLabel(pick)}</span>
      </span>
    );
  }

  return (
    <span className="predicted-outcome predicted-outcome--inline" title={reason ?? undefined}>
      <span className="predicted-outcome__label">AI</span>
      <span className="predicted-outcome__score">{score}</span>
      <span className="predicted-outcome__pick">{pickCodeLabel(pick)}</span>
    </span>
  );
}
