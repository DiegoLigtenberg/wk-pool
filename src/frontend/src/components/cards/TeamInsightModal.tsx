import { useEffect, useRef } from "react";
import type { TeamInsight } from "../../types";
import { TeamLabel } from "./TeamLabel";
import { TierBadge } from "./TierBadge";
import "./TeamInsightModal.css";

type TeamInsightModalProps = {
  insight: TeamInsight | null;
  onClose: () => void;
};

export function TeamInsightModal({ insight, onClose }: TeamInsightModalProps) {
  const modalRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!insight) {
      return;
    }

    previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    closeButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key === "Tab") {
        trapFocus(event, modalRef.current);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previousFocusRef.current?.focus();
      previousFocusRef.current = null;
    };
  }, [insight, onClose]);

  if (!insight) {
    return null;
  }

  return (
    <div className="team-insight-backdrop" role="presentation" onClick={onClose}>
      <article
        ref={modalRef}
        className="team-insight-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="team-insight-title"
        aria-describedby="team-insight-summary"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
      >
        <button ref={closeButtonRef} type="button" className="team-insight-close" onClick={onClose}>
          Sluiten
        </button>
        <p className="eyebrow">Teamvisie</p>
        <h2 id="team-insight-title">
          <TeamLabel team={insight.team} /> <TierBadge tier={insight.tier} />
        </h2>
        <p id="team-insight-summary">{insight.summary}</p>
        {insight.style ? (
          <p className="team-insight-style">
            <span className="team-insight-style__label">Speelstijl</span>
            {insight.style}
          </p>
        ) : null}
        <GroupProgram
          group={insight.group}
          opponents={insight.opponents}
          fixtures={insight.groupContext}
        />
        {insight.powerScore != null ? (
          <p className="team-insight-score">
            <span className="team-insight-score__label">Basisscore</span>
            <span className="team-insight-score__value">{insight.powerScore}</span>
            <span className="team-insight-score__hint">
              Vaste teamsterkte in het model; per wedstrijd komt daar duelcontext bij (wedstrijdscore).
            </span>
          </p>
        ) : null}
        {insight.distinctiveSpark ? (
          <section className="team-insight-spark-block" aria-label="Opvallend bij dit team">
            <h3 className="team-insight-spark__title">Opvallend bij dit team</h3>
            <p className="team-insight-spark">{insight.distinctiveSpark}</p>
          </section>
        ) : null}
        <div className="team-insight-grid">
          <InsightList title="Sterktes" items={insight.strengths} />
          <InsightList title="Risico's" items={insight.risks} />
          {insight.niche?.length ? <InsightList title="Niche signalen" items={insight.niche} /> : null}
        </div>
      </article>
    </div>
  );
}

function trapFocus(event: KeyboardEvent, container: HTMLElement | null) {
  if (!container) {
    return;
  }

  const focusableElements = Array.from(
    container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => !element.hasAttribute("hidden"));

  if (!focusableElements.length) {
    event.preventDefault();
    container.focus();
    return;
  }

  const first = focusableElements[0];
  const last = focusableElements[focusableElements.length - 1];

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function GroupProgram({
  group,
  opponents,
  fixtures,
}: {
  group?: string;
  opponents?: string[];
  fixtures?: string[];
}) {
  if (!group) {
    return null;
  }

  const hasFixtures = Boolean(fixtures?.length);
  const hasOpponents = Boolean(opponents?.length);

  if (!hasFixtures && !hasOpponents) {
    return null;
  }

  return (
    <section className="team-insight-group-program" aria-label={`Groep ${group}`}>
      <h3 className="team-insight-group-program__title">Groep {group}</h3>
      {hasFixtures ? (
        <ul className="team-insight-group-program__fixtures">
          {fixtures!.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : (
        <p className="team-insight-group-program__opponents">Tegen {opponents!.join(", ")}</p>
      )}
    </section>
  );
}

function InsightList({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h3>{title}</h3>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}-${item}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
