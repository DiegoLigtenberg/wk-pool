import type { CrystalBallBonusQuestion, CrystalBallLiveStats, CrystalBallView as CrystalBallData } from "../../types";
import { TeamLabel } from "../cards/TeamLabel";
import "./CrystalBallView.css";

type CrystalBallViewProps = {
  crystalBall: CrystalBallData;
};

const LIVE_BONUS_IDS = new Set(["yellow_cards_total", "direct_red_cards"]);

export function CrystalBallView({ crystalBall }: CrystalBallViewProps) {
  const winners =
    crystalBall.groupWinners.length > 0
      ? crystalBall.groupWinners
      : crystalBall.projectedGroups
          .filter((group) => group.winner)
          .map((group) => ({ group: group.name, team: group.winner as string }));

  return (
    <section className="panel" id="crystal-ball">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Crystal Ball</p>
          <h2>Toernooi-voorspellingen</h2>
          {crystalBall.contextAsOf ? (
            <p className="muted crystal-meta">
              Groepswinnaars uit alle 72 AI 1/2/3-picks · bonus onderzoek t/m {crystalBall.contextAsOf}
            </p>
          ) : null}
        </div>
      </div>

      <LiveStatsPanel liveStats={crystalBall.liveStats} />

      <div className="crystal-layout">
        <div>
          <div className="section-label">Groepswinnaars (uit AI-picks)</div>
          <div className="winner-grid">
            {winners.map((entry) => (
              <article className="winner-card" key={entry.group}>
                <span>Poule {entry.group}</span>
                <strong>
                  <TeamLabel team={entry.team} />
                </strong>
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

function LiveStatsPanel({ liveStats }: { liveStats: CrystalBallLiveStats }) {
  const hasSync = liveStats.updatedAt !== null;

  return (
    <section className="crystal-live-panel" aria-label="Live statistieken uit API-Football">
      <div className="crystal-live-panel__header">
        <div>
          <p className="section-label">Live statistieken (API)</p>
          <p className="crystal-live-panel__note">
            Wordt automatisch bijgewerkt via de cron sync op de backend (na elke afgeronde wedstrijd).
          </p>
        </div>
        <p className="crystal-live-panel__sync muted">
          {hasSync ? `Laatste sync: ${formatSyncTime(liveStats.updatedAt)}` : "Nog geen sync — start bij eerste WK-uitslagen"}
        </p>
      </div>
      <div className="crystal-live-grid">
        <LiveStatCard
          label="Uitslagen binnen"
          value={`${liveStats.completedMatches} / ${liveStats.totalMatches}`}
          helper="Wedstrijden met score uit API-Football"
        />
        <LiveStatCard
          label="Gele kaarten"
          value={String(liveStats.yellowCards)}
          helper="Totaal t/m nu (pool-telling)"
        />
        <LiveStatCard
          label="Direct rood"
          value={String(liveStats.directRedCards)}
          helper="Geen 2e-geel uitsluitingen"
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
  const liveValue = liveValueFor(question.id, liveStats);
  const predicted = Number.parseInt(question.value, 10);

  return (
    <article className="bonus-card">
      <span>{question.label}</span>
      <strong>{question.value}</strong>
      {liveValue !== null ? (
        <p className="bonus-live">
          Live nu: <strong>{liveValue}</strong>
          {Number.isFinite(predicted) ? (
            <>
              {" "}
              · voorspeld: {predicted}
              {liveValue > predicted ? " (boven voorspelling)" : liveValue < predicted ? " (onder voorspelling)" : " (op voorspelling)"}
            </>
          ) : null}
        </p>
      ) : null}
      <p>{question.helper}</p>
    </article>
  );
}

function liveValueFor(questionId: string, liveStats: CrystalBallLiveStats): number | null {
  if (!LIVE_BONUS_IDS.has(questionId)) {
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
