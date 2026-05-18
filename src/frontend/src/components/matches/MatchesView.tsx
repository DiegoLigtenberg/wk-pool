import { useMemo, useState } from "react";
import { formatDateShort, formatTime, phaseLabel } from "../../lib/format";
import { displayTeamName } from "../../lib/teams";
import { phaseSelectOptions, STATUS_FILTER_OPTIONS, teamSelectOptions } from "../../lib/tournament";
import type { Match, MatchPhaseFilter, MatchStatusFilter, TournamentView } from "../../types";
import { TeamLabel } from "../cards/TeamLabel";
import { StatsChips } from "../cards/StatsChips";
import { CustomSelect } from "../filters/CustomSelect";
import "./MatchesView.css";

type MatchesViewProps = {
  matches: Match[];
  summary: TournamentView["summary"];
};

const DEFAULT_STATUS: MatchStatusFilter = "all";
const DEFAULT_TEAM = "";
const DEFAULT_PHASE: MatchPhaseFilter = "all";

export function MatchesView({ matches, summary }: MatchesViewProps) {
  const [status, setStatus] = useState<MatchStatusFilter>(DEFAULT_STATUS);
  const [team, setTeam] = useState(DEFAULT_TEAM);
  const [phase, setPhase] = useState<MatchPhaseFilter>(DEFAULT_PHASE);
  const teamOptions = useMemo(() => teamSelectOptions(matches), [matches]);
  const phaseOptions = useMemo(() => phaseSelectOptions(matches), [matches]);

  const setStatusFilter = (value: MatchStatusFilter) => {
    setStatus(value);
    setTeam(DEFAULT_TEAM);
    setPhase(DEFAULT_PHASE);
  };

  const setTeamFilter = (value: string) => {
    setTeam(value);
    setStatus(DEFAULT_STATUS);
    setPhase(DEFAULT_PHASE);
  };

  const setPhaseFilter = (value: MatchPhaseFilter) => {
    setPhase(value);
    setStatus(DEFAULT_STATUS);
    setTeam(DEFAULT_TEAM);
  };

  const filteredMatches = matches.filter((match) => {
    const matchesStatus = status === "all" || match.status === status;
    const matchesTeam = !team || match.homeTeam === team || match.awayTeam === team;
    const matchesPhase = phase === "all" || match.stage === phase || phase === `group:${match.group ?? ""}`;
    return matchesStatus && matchesTeam && matchesPhase;
  });

  return (
    <section className="panel" id="wedstrijden">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Wedstrijden</p>
          <h2>Volledig wedstrijdschema</h2>
        </div>
        <StatsChips matches={matches} summary={summary} />
      </div>
      <div className="match-table">
        <div className="match-table-toolbar">
          <div className="match-filter-cell match-filter-cell--date">
            <span className="filter-label" id="status-filter-label">Toon</span>
            <CustomSelect
              id="status-filter"
              labelId="status-filter-label"
              value={status}
              options={STATUS_FILTER_OPTIONS}
              onChange={(value) => setStatusFilter(value as MatchStatusFilter)}
            />
          </div>
          <div className="match-filter-cell match-filter-cell--match">
            <span className="filter-label" id="team-filter-label">Land</span>
            <CustomSelect id="team-filter" labelId="team-filter-label" value={team} options={teamOptions} onChange={setTeamFilter} scroll centered />
          </div>
          <div className="match-filter-cell match-filter-cell--group">
            <span className="filter-label" id="phase-filter-label">Fase</span>
            <CustomSelect
              id="phase-filter"
              labelId="phase-filter-label"
              value={phase}
              options={phaseOptions}
              onChange={(value) => setPhaseFilter(value as MatchPhaseFilter)}
              scroll
            />
          </div>
        </div>
        <div className="match-table-head">
          <span>Datum</span>
          <span>Wedstrijd</span>
          <span>Fase</span>
        </div>
        <div id="match-table-body">
          {filteredMatches.length ? (
            filteredMatches.map((match) => <FixtureRow key={match.matchNumber} match={match} />)
          ) : (
            <div className="empty-state">Geen wedstrijden gevonden voor deze filters.</div>
          )}
        </div>
      </div>
    </section>
  );
}

function FixtureRow({ match }: { match: Match }) {
  const aiPick = match.aiPrediction.pick;
  const homeOutcome = teamOutcome(match, "home");
  const awayOutcome = teamOutcome(match, "away");
  const [showPrediction, setShowPrediction] = useState(false);
  const predictionId = `prediction-${match.matchNumber}`;
  const aiLabel = `Toon AI-uitleg voor ${displayTeamName(match.homeTeam)} tegen ${displayTeamName(match.awayTeam)}`;

  return (
    <article className={`fixture-row ${match.status}`}>
      <div className="date-cell">
        <strong>{formatDateShort(match.kickoffAt)}</strong>
        <span>{formatTime(match.kickoffAt)}</span>
      </div>
      <div className="match-cell">
        <div className="scoreboard-line">
          <span className={`team-pick ${homeOutcome}`}>
            <span className="team-with-ai team-with-ai--home">
              {aiPick === "1" ? (
                <AiBadge
                  status={match.aiPrediction.status}
                  matchStatus={match.status}
                  label={aiLabel}
                  expanded={showPrediction}
                  controls={predictionId}
                  onClick={() => setShowPrediction((current) => !current)}
                />
              ) : (
                <AiMarkerSlot />
              )}
              <TeamLabel team={match.homeTeam} compact truncate={false} />
            </span>
          </span>
          <span className="result-stack">
            {aiPick === "3" ? (
              <AiBadge
                status={match.aiPrediction.status}
                matchStatus={match.status}
                label={aiLabel}
                expanded={showPrediction}
                controls={predictionId}
                pickKind="draw"
                onClick={() => setShowPrediction((current) => !current)}
              />
            ) : null}
            <strong className={`result-pill${match.score ? "" : " result-upcoming"}`}>
              {match.score ? `${match.score.home} - ${match.score.away}` : "-"}
            </strong>
          </span>
          <span className={`team-pick ${awayOutcome}`}>
            <span className="team-with-ai team-with-ai--away">
              {aiPick === "2" ? (
                <AiBadge
                  status={match.aiPrediction.status}
                  matchStatus={match.status}
                  label={aiLabel}
                  expanded={showPrediction}
                  controls={predictionId}
                  onClick={() => setShowPrediction((current) => !current)}
                />
              ) : (
                <AiMarkerSlot />
              )}
              <TeamLabel team={match.awayTeam} compact truncate={false} />
            </span>
          </span>
        </div>
        {showPrediction ? <PredictionPanel id={predictionId} match={match} /> : null}
      </div>
      <div className="group-cell">
        <strong>{phaseLabel(match)}</strong>
      </div>
    </article>
  );
}

function AiMarkerSlot() {
  return <span className="ai-marker-slot" aria-hidden />;
}

function aiMarkerTitle(status: Match["aiPrediction"]["status"], matchStatus: Match["status"], pickKind?: "team" | "draw"): string {
  if (matchStatus === "upcoming") {
    return pickKind === "draw" ? "AI voorspelde gelijk — wedstrijd nog niet gespeeld" : "AI-tip nog niet af te rekenen";
  }
  if (status === "correct") {
    return pickKind === "draw" ? "AI voorspelde gelijk juist" : "AI-tip: juist voorspeld";
  }
  if (status === "wrong") {
    return pickKind === "draw" ? "AI voorspelde gelijk, maar niet juist" : "AI-tip: niet juist voorspeld";
  }
  return "AI-tip";
}

function AiBadge({
  status,
  matchStatus,
  label,
  expanded,
  controls,
  pickKind = "team",
  onClick,
}: {
  status: Match["aiPrediction"]["status"];
  matchStatus: Match["status"];
  label: string;
  expanded: boolean;
  controls: string;
  pickKind?: "team" | "draw";
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`ai-marker ai-marker-button ${pickKind === "draw" ? "ai-marker--draw-tip" : ""} ${status}`}
      title={aiMarkerTitle(status, matchStatus, pickKind)}
      onClick={onClick}
      aria-label={label}
      aria-expanded={expanded}
      aria-controls={expanded ? controls : undefined}
    >
      AI
    </button>
  );
}

function PredictionPanel({ id, match }: { id: string; match: Match }) {
  const prediction = match.aiPrediction;
  return (
    <section className="prediction-panel" id={id}>
      <div>
        <span className="prediction-label">AI voorspelling</span>
        <strong>{predictionTitle(match)}</strong>
      </div>
      <div className="prediction-probabilities">
        <span>{displayTeamName(match.homeTeam)} {formatProbability(prediction.homeWinProbability)}</span>
        {prediction.drawProbability !== null ? <span>Gelijk {formatProbability(prediction.drawProbability)}</span> : null}
        <span>{displayTeamName(match.awayTeam)} {formatProbability(prediction.awayWinProbability)}</span>
      </div>
      <p>{prediction.explanation}</p>
      <div className="prediction-themes">
        {prediction.themes.map((theme) => (
          <span key={theme}>{theme}</span>
        ))}
      </div>
    </section>
  );
}

function predictionTitle(match: Match): string {
  if (match.aiPrediction.pick === "1") {
    return `${displayTeamName(match.homeTeam)} wint · ${match.aiPrediction.confidence}%`;
  }
  if (match.aiPrediction.pick === "2") {
    return `${displayTeamName(match.awayTeam)} wint · ${match.aiPrediction.confidence}%`;
  }
  if (match.aiPrediction.confidence === 0) {
    return "Wacht op bekende landen";
  }
  return `Gelijkspel · ${match.aiPrediction.confidence}%`;
}

function formatProbability(value: number | null): string {
  return value === null ? "-" : `${value}%`;
}

function teamOutcome(match: Match, side: "home" | "away"): "winner" | "loser" | "draw" | "" {
  if (!match.score) {
    return "";
  }

  if (match.score.home === match.score.away) {
    return "draw";
  }

  const won = side === "home" ? match.score.home > match.score.away : match.score.away > match.score.home;
  return won ? "winner" : "loser";
}
