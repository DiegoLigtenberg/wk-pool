import type { CrystalBallView as CrystalBallData } from "../../types";
import { TeamLabel } from "../cards/TeamLabel";
import "./CrystalBallView.css";

type CrystalBallViewProps = {
  crystalBall: CrystalBallData;
};

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
              <BonusCard
                key={question.id}
                label={question.label}
                value={question.value}
                helper={question.helper}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function BonusCard({ label, value, helper }: { label: string; value: string; helper: string }) {
  return (
    <article className="bonus-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </article>
  );
}
