import { countryCodeForTeam, displayTeamName, truncateLabel } from "../../lib/teams";
import "./cards.css";

type TeamLabelProps = {
  team: string;
  compact?: boolean;
};

export function TeamLabel({ team, compact = false }: TeamLabelProps) {
  const fullName = displayTeamName(team);
  const label = compact ? truncateLabel(fullName, 12) : fullName;
  const code = countryCodeForTeam(team);

  return (
    <span className={`team-label${compact ? " team-label--compact" : ""}`}>
      {code ? (
        <img className="flag" src={`https://flagcdn.com/w40/${code}.png`} alt="" loading="lazy" />
      ) : (
        <span className="flag flag-placeholder" />
      )}
      <span title={fullName}>{label}</span>
    </span>
  );
}
