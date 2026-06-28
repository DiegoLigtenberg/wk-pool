import { Bracket } from "react-bracket-ui";
import { useEffect, useMemo, useRef } from "react";
import type { Match as BracketMatch } from "react-bracket-ui";
import { flattenKnockoutBracket, knockoutBracketRound, knockoutNextMatchId } from "../../lib/knockoutBracket";
import { formatSuggestedScore, showsKnockoutScorePrediction } from "../../lib/prediction";
import { displayTeamName } from "../../lib/teams";
import type { Match } from "../../types";
import { TeamLabel } from "../cards/TeamLabel";
import "./KnockoutView.css";

type KnockoutViewProps = {
  knockoutMatches: Match[];
};

export function KnockoutView({ knockoutMatches }: KnockoutViewProps) {
  // Round titles must match knockout rows in `Round Number` (CSV); backend tests lock the same labels.
  const round32 = round(knockoutMatches, "Round of 32");
  const round16 = round(knockoutMatches, "Round of 16");
  const quarter = round(knockoutMatches, "Quarter Finals");
  const semi = round(knockoutMatches, "Semi Finals");
  const finals = round(knockoutMatches, "Finals");
  const final = finals.find((match) => match.matchNumber === 104) ?? finals[finals.length - 1];
  const thirdPlace = finals.find((match) => match.matchNumber !== final?.matchNumber);
  const bracketMatches = toBracketMatches(round32, round16, quarter, semi, final);
  const orderedBracketMatches = useMemo(
    () => flattenKnockoutBracket(round32, round16, quarter, semi, final),
    [round32, round16, quarter, semi, final],
  );
  const bracketCardMeta = useMemo(
    () => orderedBracketMatches.map((match) => bracketCardMetaFor(match)),
    [orderedBracketMatches],
  );
  const bracketShellRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cards = bracketShellRef.current?.querySelectorAll<HTMLElement>(".wk-bracket .relative");
    cards?.forEach((card, index) => {
      const meta = bracketCardMeta[index];
      if (!meta) {
        return;
      }
      card.dataset.date = meta.date;
      card.dataset.status = meta.status;
      if (meta.prediction) {
        card.dataset.prediction = meta.prediction;
      } else {
        delete card.dataset.prediction;
      }
    });
  }, [bracketCardMeta]);

  return (
    <section className="panel" id="knockout">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Knock-out</p>
          <h2>Knock-outfase</h2>
        </div>
      </div>
      <p className="panel-subnote">
        Het schema loopt van zestiende finale tot finale. Groene markering = echte winnaar. AI-voorspellingen
        (Voorsp.) gelden alleen voor nog niet gespeelde duels met bekende teams.
      </p>
      <div className="knockout-bracket-shell" ref={bracketShellRef}>
        <Bracket
          className="wk-bracket"
          matches={bracketMatches}
          showRoundNames
          roundNames={{
            1: "Zestiende finale",
            2: "Achtste finale",
            3: "Kwartfinale",
            4: "Halve finale",
            5: "Finale",
          }}
          matchWidth={230}
          matchHeight={128}
          gap={24}
          colors={{
            background: "#0f172a",
            primary: "#76a5eb",
            secondary: "#94a3b8",
            winner: "rgba(34, 197, 94, 0.18)",
          }}
          style={{
            height: "auto",
            minHeight: 0,
            overflow: "visible",
            padding: "1rem",
          }}
        />
      </div>
      {thirdPlace ? (
        <aside className="third-place-card" aria-label="Troostfinale">
          <div>
            <p className="eyebrow">Troostfinale</p>
            <strong>{formatKnockoutDate(thirdPlace)}</strong>
          </div>
          <div className="third-place-match">
            <div className="third-place-team">
              <TeamLabel team={thirdPlace.homeTeam} />
            </div>
            <div className="third-place-team">
              <TeamLabel team={thirdPlace.awayTeam} />
            </div>
          </div>
        </aside>
      ) : null}
    </section>
  );
}

function toBracketMatches(
  round32: Match[],
  round16: Match[],
  quarter: Match[],
  semi: Match[],
  final?: Match,
): BracketMatch[] {
  return flattenKnockoutBracket(round32, round16, quarter, semi, final).map((match) =>
    toBracketMatch(match, knockoutBracketRound(match), knockoutNextMatchId(match.matchNumber)),
  );
}

function toBracketMatch(match: Match, roundNumber: number, nextMatchId: number | null): BracketMatch {
  const scores = realParticipantScores(match);

  return {
    id: match.matchNumber,
    round: roundNumber,
    matchNumber: match.matchNumber,
    nextMatchId,
    winner: actualWinnerId(match),
    participant1: {
      id: `${match.matchNumber}-home`,
      name: displayTeamName(match.homeTeam),
      score: scores.home,
    },
    participant2: {
      id: `${match.matchNumber}-away`,
      name: displayTeamName(match.awayTeam),
      score: scores.away,
    },
  };
}

function bracketCardMetaFor(match: Match): {
  date: string;
  status: "played" | "predicted" | "upcoming";
  prediction: string;
} {
  const date = formatKnockoutDateLines(match);
  if (match.score) {
    return { date, status: "played", prediction: "" };
  }
  if (showsKnockoutScorePrediction(match)) {
    return {
      date,
      status: "predicted",
      prediction: `Voorsp. ${formatSuggestedScore(match)}`,
    };
  }
  return { date, status: "upcoming", prediction: "" };
}

function realParticipantScores(match: Match): { home?: number; away?: number } {
  if (!match.score) {
    return {};
  }
  return { home: match.score.home, away: match.score.away };
}

function actualWinnerId(match: Match): string | null {
  if (!match.score) {
    return null;
  }
  if (match.score.home > match.score.away) {
    return `${match.matchNumber}-home`;
  }
  if (match.score.away > match.score.home) {
    return `${match.matchNumber}-away`;
  }
  return null;
}

function formatKnockoutDate(match: Match): string {
  return new Intl.DateTimeFormat("nl-NL", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(match.kickoffAt));
}

function formatKnockoutDateLines(match: Match): string {
  const date = new Date(match.kickoffAt);
  const dayMonth = new Intl.DateTimeFormat("nl-NL", {
    day: "numeric",
    month: "short",
  }).format(date);
  const time = new Intl.DateTimeFormat("nl-NL", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);

  return `${dayMonth}\n${time}`;
}

function round(matches: Match[], roundName: string): Match[] {
  return matches
    .filter((match) => match.round === roundName)
    .sort((first, second) => first.matchNumber - second.matchNumber);
}
