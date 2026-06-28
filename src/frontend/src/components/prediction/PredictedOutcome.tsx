import type { Match } from "../../types";
import {
  formatSuggestedScore,
  pickCodeLabel,
  pickOutcomeLabel,
  showsKnockoutScorePrediction,
} from "../../lib/prediction";
import "./PredictedOutcome.css";

type PredictedOutcomeProps = {
  match: Match;
  variant?: "panel" | "card" | "row";
};

/** Score + toto voorspelling — alleen knock-out met bekende teams. */
export function PredictedOutcome({ match, variant = "row" }: PredictedOutcomeProps) {
  if (!showsKnockoutScorePrediction(match)) {
    return null;
  }

  const score = formatSuggestedScore(match)!;
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

  if (variant === "card") {
    return (
      <div className="knockout-prediction-card" title={reason ?? undefined}>
        <strong className="knockout-prediction-card__score">{score}</strong>
      </div>
    );
  }

  return (
    <div className="knockout-prediction-row" title={`AI-voorspelling (90 min): ${reason ?? score}`}>
      <span className="knockout-prediction-row__label">Voorsp.</span>
      <span className="knockout-prediction-row__score">{score}</span>
    </div>
  );
}
