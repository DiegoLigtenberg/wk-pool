import { forwardRef, type RefObject } from "react";
import type { Match, PredictionFactor, PredictionInsight, PredictionScoreSide } from "../../types";
import { displayTeamName } from "../../lib/teams";
import { PredictedOutcome } from "../prediction/PredictedOutcome";

type PredictionPanelProps = {
  id: string;
  match: Match;
  onClose: () => void;
  closeButtonRef: RefObject<HTMLButtonElement | null>;
};

export const PredictionPanel = forwardRef<HTMLElement, PredictionPanelProps>(function PredictionPanel(
  { id, match, onClose, closeButtonRef },
  ref,
) {
  const prediction = match.aiPrediction;
  const insight = prediction.insight;
  const presentation = insight ? presentInsight(insight) : null;

  return (
    <section
      ref={ref}
      className="prediction-panel"
      id={id}
      role="region"
      aria-labelledby={`${id}-title`}
      tabIndex={-1}
    >
      <div className="prediction-panel-header">
        <div>
          <span className="prediction-label">AI voorspelling</span>
          <strong id={`${id}-title`}>{predictionTitle(match)}</strong>
        </div>
        <button ref={closeButtonRef} type="button" className="prediction-panel-close" onClick={onClose}>
          Sluiten
        </button>
      </div>

      <Probabilities match={match} highlightedPick={prediction.pick} />
      <PredictedOutcome match={match} variant="panel" />

      {presentation ? (
        <>
          <p className="prediction-verdict prediction-verdict--lead">{presentation.verdict}</p>
          {presentation.legacyHint ? (
            <p className="prediction-legacy-hint">{presentation.legacyHint}</p>
          ) : null}
          {presentation.leadSummary ? (
            <p className="prediction-lead-summary">{presentation.leadSummary}</p>
          ) : null}
          <details className="prediction-details">
            <summary>Scores en research-details</summary>
            {presentation.intro ? <p className="prediction-intro">{presentation.intro}</p> : null}
            {presentation.scoreSummary ? (
              <p className="prediction-score-summary">{presentation.scoreSummary}</p>
            ) : null}
            <div className="prediction-score-grid">
              <TeamScoreCard side={presentation.home} />
              <TeamScoreCard side={presentation.away} />
            </div>
          </details>
        </>
      ) : (
        <p className="prediction-verdict">{prediction.explanation}</p>
      )}
    </section>
  );
});

type Presentation = PredictionInsight & {
  intro?: string;
  leadSummary?: string;
  legacyHint?: string;
};

function presentInsight(insight: PredictionInsight): Presentation {
  const modelStep = insight.steps?.find((s) => s.title === "Hoe dit werkt");
  const duelStep = insight.steps?.find((s) => s.title === "Belangrijk in dit duel");
  const leadSummary =
    insight.leadSummary ?? duelStep?.body ?? insight.steps?.[1]?.body;

  if (modelStep && leadSummary) {
    return {
      ...insight,
      intro: modelStep.body,
      leadSummary,
    };
  }

  return {
    ...insight,
    intro: insight.steps?.[0]?.body,
    leadSummary: leadSummary ?? insight.narrative,
    legacyHint: "Herstart de backend voor de nieuwste uitleg (poetry run wk-pool-backend).",
  };
}

function Probabilities({
  match,
  highlightedPick,
}: {
  match: Match;
  highlightedPick: Match["aiPrediction"]["pick"];
}) {
  const prediction = match.aiPrediction;
  return (
    <div className="prediction-probabilities" role="list" aria-label="Kansen">
      <span className={highlightedPick === "1" ? "is-pick" : undefined} role="listitem">
        {displayTeamName(match.homeTeam)} {formatProbability(prediction.homeWinProbability)}
      </span>
      {prediction.drawProbability !== null ? (
        <span className={highlightedPick === "3" ? "is-pick" : undefined} role="listitem">
          Gelijk {formatProbability(prediction.drawProbability)}
        </span>
      ) : null}
      <span className={highlightedPick === "2" ? "is-pick" : undefined} role="listitem">
        {displayTeamName(match.awayTeam)} {formatProbability(prediction.awayWinProbability)}
      </span>
    </div>
  );
}

function TeamScoreCard({ side }: { side: PredictionScoreSide }) {
  const matchFactors = side.factors.filter((f) => f.scope === "match");
  const teamFactors = side.factors.filter((f) => f.scope === "team");
  const active = side.factors.filter((f) => f.delta !== 0);

  return (
    <article className="prediction-team-card">
      <header className="prediction-team-card__header">
        <h3>{side.team}</h3>
        <p className="prediction-team-card__score-line">
          Basis {side.powerScore}
          {side.contextDelta !== 0 ? (
            <>
              {" "}
              <span className="prediction-team-card__ctx">{formatSigned(side.contextDelta)}</span>
            </>
          ) : null}
          {" → dueltotaal "}
          <span className="prediction-team-card__eff">{side.effectiveScore}</span>
        </p>
      </header>
      {active.length === 0 ? (
        <p className="prediction-team-card__empty">Geen extra onderdelen voor dit duel.</p>
      ) : (
        <>
          <FactorGroup title="Dit duel" factors={matchFactors} />
          <FactorGroup title="Hele groepsfase" factors={teamFactors} />
        </>
      )}
    </article>
  );
}

function FactorGroup({ title, factors }: { title: string; factors: PredictionFactor[] }) {
  const visible = factors.filter((f) => f.delta !== 0);
  if (visible.length === 0) {
    return null;
  }
  return (
    <div className="prediction-factor-group">
      <h4>{title}</h4>
      <ul>
        {visible.map((factor) => (
          <li key={`${factor.id}-${factor.reason}`} className={factor.delta > 0 ? "is-plus" : "is-minus"}>
            <span className="prediction-factor-delta">{formatSigned(factor.delta)}</span>
            <span className="prediction-factor-body">
              <strong>{factor.label}</strong>
              <span>{factor.reason}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function predictionTitle(match: Match): string {
  return `${displayTeamName(match.homeTeam)} - ${displayTeamName(match.awayTeam)}`;
}

function formatProbability(value: number | null): string {
  return value === null ? "-" : `${value}%`;
}

function formatSigned(value: number): string {
  return value > 0 ? `+${value}` : `${value}`;
}
