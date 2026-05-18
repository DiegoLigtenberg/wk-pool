import { countryCodeForTeam, displayTeamName, truncateLabel } from "../../lib/teams";
import "./cards.css";
import { useTeamInsight } from "./TeamInsightContext";

type TeamLabelProps = {
  team: string;
  compact?: boolean;
  maxLength?: number;
};

export function TeamLabel({ team, compact = false, maxLength }: TeamLabelProps) {
  const fullName = displayTeamName(team);
  const labelLimit = maxLength ?? (compact ? 12 : undefined);
  const label = labelLimit ? truncateLabel(fullName, labelLimit) : fullName;
  const code = countryCodeForTeam(team);
  const { insight, open } = useTeamInsight(team);
  const content = (
    <>
      {code ? (
        <img className="flag" src={`https://flagcdn.com/w40/${code}.png`} alt="" loading="lazy" referrerPolicy="no-referrer" />
      ) : (
        <span className="flag flag-placeholder" />
      )}
      <span title={fullName}>{label}</span>
    </>
  );

  if (insight && open) {
    return (
      <button
        type="button"
        className={`team-label team-label-button${compact ? " team-label--compact" : ""}`}
        onClick={open}
        aria-label={`Open teamvisie voor ${fullName}`}
      >
        {content}
      </button>
    );
  }

  return (
    <span className={`team-label${compact ? " team-label--compact" : ""}`}>
      {content}
    </span>
  );
}
