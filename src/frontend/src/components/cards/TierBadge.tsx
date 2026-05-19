import { useId } from "react";
import { TIER_LADDER, tierRank } from "../../lib/tiers";
import "./TierBadge.css";

type TierBadgeProps = {
  tier: string;
};

export function TierBadge({ tier }: TierBadgeProps) {
  const rank = tierRank(tier);
  const hintId = useId();

  return (
    <span className="tier-badge">
      <span
        className="tier-badge__label"
        tabIndex={0}
        aria-describedby={hintId}
        title={rank ? `Rang ${rank} van ${TIER_LADDER.length} in het model` : undefined}
      >
        {tier}
        {rank ? (
          <span className="tier-badge__rank-sup" aria-hidden="true">
            {rank}
          </span>
        ) : null}
      </span>
      <span className="tier-badge__tooltip" id={hintId} role="tooltip">
        <span className="tier-badge__tooltip-title">Rangorde in het model</span>
        <ol className="tier-badge__ladder">
          {TIER_LADDER.map((name, index) => (
            <li key={name} className={name === tier ? "is-current" : undefined}>
              <span className="tier-badge__rank">{index + 1}</span>
              {name}
            </li>
          ))}
        </ol>
      </span>
    </span>
  );
}
