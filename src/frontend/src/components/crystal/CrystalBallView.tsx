import type {
  CrystalBallBonusQuestion,
  CrystalBallGroupWinner,
  CrystalBallLiveStats,
  CrystalBallView as CrystalBallData,
  PredictionStatus,
} from "../../types";
import { TeamLabel } from "../cards/TeamLabel";
import "./CrystalBallView.css";

type CrystalBallViewProps = {
  crystalBall: CrystalBallData;
};

const LIVE_COUNT_BONUS_IDS = new Set(["yellow_cards_total", "direct_red_cards"]);

export function CrystalBallView({ crystalBall }: CrystalBallViewProps) {
  const winners: CrystalBallGroupWinner[] =
    crystalBall.groupWinners.length > 0
      ? crystalBall.groupWinners
      : crystalBall.projectedGroups
          .filter((group) => group.winner)
          .map((group) => ({
            group: group.name,
            team: group.winner as string,
            status: "pending" as const,
          }));

  return (
    <section className="panel" id="crystal-ball">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Crystal Ball</p>
          <h2>Toernooi-voorspellingen</h2>
        </div>
      </div>

      <LiveStatsPanel liveStats={crystalBall.liveStats} />

      <div className="crystal-layout">
        <div>
          <div className="section-label">Groepswinnaars</div>
          <div className="winner-grid">
            {winners.map((entry) => (
              <article className={`winner-card ai-${entry.status}`} key={entry.group}>
                <span>Poule {entry.group}</span>
                <strong>
                  <TeamLabel team={entry.team} />
                </strong>
                <p className="winner-card__status">
                  <span className={`legend-dot legend-dot--${entry.status}`} />
                  {groupWinnerStatusText(entry.status)}
                </p>
              </article>
            ))}
          </div>
        </div>
        <div>
          <div className="section-label">Bonusvragen</div>
          <div className="bonus-grid">
            {crystalBall.bonusQuestions.map((question) => (
              <BonusCard key={question.id} question={question} liveStats={crystalBall.liveStats} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function groupWinnerStatusText(status: PredictionStatus): string {
  if (status === "correct") {
    return "Leidt nu ook in de live stand";
  }
  if (status === "wrong") {
    return "Leidt nu een ander land";
  }
  return "Nog af te rekenen";
}

function LiveStatsPanel({ liveStats }: { liveStats: CrystalBallLiveStats }) {
  const hasResults = liveStats.completedMatches > 0;
  const topScorerLabel = formatTopScorer(liveStats.topScorer);

  return (
    <section className="crystal-live-panel" aria-label="Stand van zaken">
      <div className="crystal-live-panel__header">
        <p className="section-label">Stand van zaken</p>
        {liveStats.updatedAt ? (
          <p className="crystal-live-panel__sync muted">Bijgewerkt {formatSyncTime(liveStats.updatedAt)}</p>
        ) : null}
      </div>
      <div className="crystal-live-grid">
        <LiveStatCard
          label="Uitslagen"
          value={`${liveStats.completedMatches} / ${liveStats.totalMatches}`}
          helper={hasResults ? "Wedstrijden met uitslag" : "Volgt zodra het WK begint"}
        />
        <LiveStatCard
          label="Gele kaarten"
          value={String(liveStats.yellowCards)}
          helper="2e geel telt dubbel"
        />
        <LiveStatCard
          label="Direct rood"
          value={String(liveStats.directRedCards)}
          helper="Zonder 2e-geel"
        />
        <LiveStatCard
          label="Topscorer"
          value={topScorerLabel}
          helper={hasResults ? "Hele toernooi" : "Nog geen doelpunten"}
        />
      </div>
    </section>
  );
}

function LiveStatCard({ label, value, helper }: { label: string; value: string; helper: string }) {
  return (
    <article className="live-stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </article>
  );
}

function BonusCard({
  question,
  liveStats,
}: {
  question: CrystalBallBonusQuestion;
  liveStats: CrystalBallLiveStats;
}) {
  const liveCount = liveCountFor(question.id, liveStats);
  const liveTopScorer = question.id === "top_scorer" ? liveStats.topScorer : null;
  const predicted = Number.parseInt(question.value, 10);
  const showLiveCounts = liveCount !== null && liveStats.completedMatches > 0;

  return (
    <article className="bonus-card">
      <span>{question.label}</span>
      <strong>{question.value}</strong>
      {showLiveCounts ? (
        <p className="bonus-live">
          Stand: <strong>{liveCount}</strong>
          {Number.isFinite(predicted) ? <> · voorspelling {predicted}</> : null}
        </p>
      ) : null}
      {liveTopScorer ? (
        <p className="bonus-live">
          Stand:{" "}
          <strong>
            {liveTopScorer.name}, {liveTopScorer.goals} {liveTopScorer.goals === 1 ? "goal" : "goals"}
          </strong>
          {liveTopScorer.team ? <> · {liveTopScorer.team}</> : null}
        </p>
      ) : null}
      <p>{question.helper}</p>
    </article>
  );
}

function liveCountFor(questionId: string, liveStats: CrystalBallLiveStats): number | null {
  if (!LIVE_COUNT_BONUS_IDS.has(questionId)) {
    return null;
  }
  if (questionId === "yellow_cards_total") {
    return liveStats.yellowCards;
  }
  if (questionId === "direct_red_cards") {
    return liveStats.directRedCards;
  }
  return null;
}

function formatTopScorer(topScorer: CrystalBallLiveStats["topScorer"]): string {
  if (!topScorer) {
    return "—";
  }

  const goalsLabel = topScorer.goals === 1 ? "goal" : "goals";
  if (topScorer.team) {
    return `${topScorer.name} · ${topScorer.goals} ${goalsLabel} · ${topScorer.team}`;
  }

  return `${topScorer.name} · ${topScorer.goals} ${goalsLabel}`;
}

function formatSyncTime(iso: string | null): string {
  if (!iso) {
    return "—";
  }

  return new Intl.DateTimeFormat("nl-NL", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}
