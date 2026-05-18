import type { TeamInsight } from "../../types";
import { TeamLabel } from "./TeamLabel";
import "./TeamInsightModal.css";

type TeamInsightModalProps = {
  insight: TeamInsight | null;
  onClose: () => void;
};

export function TeamInsightModal({ insight, onClose }: TeamInsightModalProps) {
  if (!insight) {
    return null;
  }

  return (
    <div className="team-insight-backdrop" role="presentation" onClick={onClose}>
      <article className="team-insight-modal" role="dialog" aria-modal="true" aria-label={`${insight.team} teamvisie`} onClick={(event) => event.stopPropagation()}>
        <button type="button" className="team-insight-close" onClick={onClose}>
          Sluiten
        </button>
        <p className="eyebrow">Teamvisie</p>
        <h2>
          <TeamLabel team={insight.team} /> <span>{insight.tier}</span>
        </h2>
        <p>{insight.summary}</p>
        <div className="team-insight-grid">
          <InsightList title="Sterktes" items={insight.strengths} />
          <InsightList title="Risico's" items={insight.risks} />
          <InsightList title="Niche signalen" items={insight.niche} />
        </div>
      </article>
    </div>
  );
}

function InsightList({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
