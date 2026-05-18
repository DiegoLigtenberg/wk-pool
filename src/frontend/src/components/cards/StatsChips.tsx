import type { Match, TournamentView } from "../../types";
import "./cards.css";

type StatsChipsProps = {
  matches: Match[];
  summary: TournamentView["summary"];
};

export function StatsChips({ matches, summary }: StatsChipsProps) {
  const played = matches.filter((match) => match.status === "completed").length;
  const aiDecided = summary.aiCorrect + summary.aiWrong;

  return (
    <div className="panel-stats" aria-label="Wedstrijdvoortgang">
      <span className="stat-chip">
        <span className="stat-value">
          {played}
          <span className="stat-divider">/</span>
          {matches.length}
        </span>
        <span className="stat-label">gespeeld</span>
      </span>
      <span className="stat-chip stat-chip--ai">
        <span className="stat-value">
          {summary.aiCorrect}
          <span className="stat-divider">/</span>
          {aiDecided}
        </span>
        <span className="stat-label">AI goed</span>
        {aiDecided > 0 ? <span className="stat-accent">{summary.aiAccuracy}%</span> : null}
      </span>
    </div>
  );
}
