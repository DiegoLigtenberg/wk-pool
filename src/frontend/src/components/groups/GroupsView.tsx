import { renderScore } from "../../lib/format";
import { groupMatches } from "../../lib/tournament";
import type { Group, Match, Standing, TournamentView } from "../../types";
import { StatsChips } from "../cards/StatsChips";
import { TeamLabel } from "../cards/TeamLabel";
import "./GroupsView.css";

type GroupsViewProps = {
  tournament: TournamentView;
};

export function GroupsView({ tournament }: GroupsViewProps) {
  const matches = groupMatches(tournament);

  return (
    <section className="panel" id="poules">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Poules</p>
          <h2>Stand en AI-uitslagen per poule</h2>
        </div>
        <StatsChips matches={matches} summary={tournament.summary} />
      </div>
      <p className="panel-subnote">
        AI-status: <span className="legend-dot legend-dot--correct" /> goed voorspeld,{" "}
        <span className="legend-dot legend-dot--wrong" /> fout voorspeld,{" "}
        <span className="legend-dot legend-dot--pending" /> nog te spelen.
      </p>
      <div className="groups-grid">{tournament.groups.map((group) => <GroupCard key={group.name} group={group} />)}</div>
    </section>
  );
}

function GroupCard({ group }: { group: Group }) {
  const winner = group.standings[0];

  return (
    <article className="group-card">
      <div className="group-header">
        <p className="eyebrow">Poule {group.name}</p>
        <h2>{winner ? <TeamLabel team={winner.team} /> : "Nog geen winnaar"}</h2>
        <p className="group-subtitle">Huidige poulewinnaar</p>
      </div>
      <div className="section-label">Stand</div>
      <div className="standings">{group.standings.map((standing, index) => <StandingRow key={standing.team} standing={standing} index={index} />)}</div>
      <div className="section-label">Wedstrijden</div>
      <div className="group-matches">{group.matches.map((match) => <CompactMatch key={match.matchNumber} match={match} />)}</div>
    </article>
  );
}

function StandingRow({ standing, index }: { standing: Standing; index: number }) {
  return (
    <div className={`standing-row${index === 0 ? " leader" : ""}`}>
      <span className="team-name">
        {index + 1}. <TeamLabel team={standing.team} />
      </span>
      <span>{standing.played}P</span>
      <span>
        {standing.wins}-{standing.draws}-{standing.losses}
      </span>
      <span>
        {standing.goalDifference >= 0 ? "+" : ""}
        {standing.goalDifference}
      </span>
      <strong>{standing.points} pts</strong>
    </div>
  );
}

function CompactMatch({ match }: { match: Match }) {
  const homeOutcome = teamOutcome(match, "home");
  const awayOutcome = teamOutcome(match, "away");

  return (
    <div className={`compact-match ai-${match.aiPrediction.status}`} title={`AI: ${aiStatusLabel(match.aiPrediction.status)}`}>
      <div className="fixture-teams">
        <span className={`team-slot team-slot--home ${homeOutcome}`}>
          <TeamLabel team={match.homeTeam} compact maxLength={11} />
        </span>
        <span className="fixture-vs">tegen</span>
        <span className={`team-slot team-slot--away ${awayOutcome}`}>
          <TeamLabel team={match.awayTeam} compact maxLength={11} />
        </span>
      </div>
      <strong className="compact-score">{match.score ? renderScore(match) : "-"}</strong>
    </div>
  );
}

function aiStatusLabel(status: Match["aiPrediction"]["status"]): string {
  if (status === "correct") {
    return "goed voorspeld";
  }
  if (status === "wrong") {
    return "fout voorspeld";
  }
  return "nog te spelen";
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
