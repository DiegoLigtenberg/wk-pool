import { Bracket } from "react-bracket-ui";
import { useEffect, useMemo, useRef } from "react";
import type { Match as BracketMatch } from "react-bracket-ui";
import { displayTeamName, hasKnownTeams } from "../../lib/teams";
import type { Match } from "../../types";
import { TeamLabel } from "../cards/TeamLabel";
import "./KnockoutView.css";

type KnockoutViewProps = {
  knockoutMatches: Match[];
};

export function KnockoutView({ knockoutMatches }: KnockoutViewProps) {
  const round32 = round(knockoutMatches, "Round of 32");
  const round16 = round(knockoutMatches, "Round of 16");
  const quarter = round(knockoutMatches, "Quarter Finals");
  const semi = round(knockoutMatches, "Semi Finals");
  const finals = round(knockoutMatches, "Finals");
  const final = finals.find((match) => match.matchNumber === 104) ?? finals[finals.length - 1];
  const thirdPlace = finals.find((match) => match.matchNumber !== final?.matchNumber);
  const bracketMatches = toBracketMatches(round16, quarter, semi, final);
  const bracketDates = useMemo(
    () => [...round16, ...quarter, ...semi, ...(final ? [final] : [])].map(formatKnockoutDateLines),
    [round16, quarter, semi, final],
  );
  const bracketShellRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cards = bracketShellRef.current?.querySelectorAll<HTMLElement>(".wk-bracket .relative");
    cards?.forEach((card, index) => {
      card.dataset.date = bracketDates[index] ?? "";
    });
  }, [bracketDates]);

  return (
    <section className="panel" id="knockout">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Knock-out</p>
          <h2>Knock-outfase</h2>
        </div>
      </div>
      <p className="panel-subnote">
        De eerste knock-outronde telt {round32.length} wedstrijden. Daarna loopt het schema hieronder van achtste finale tot finale.
      </p>
      <div className="knockout-bracket-shell" ref={bracketShellRef}>
        <Bracket
          className="wk-bracket"
          matches={bracketMatches}
          showRoundNames
          roundNames={{
            1: "Achtste finale",
            2: "Kwartfinale",
            3: "Halve finale",
            4: "Finale",
          }}
          matchWidth={230}
          matchHeight={104}
          gap={32}
          colors={{
            background: "#0f172a",
            primary: "#7dd3fc",
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
  round16: Match[],
  quarter: Match[],
  semi: Match[],
  final?: Match,
): BracketMatch[] {
  const nextMatchIds = new Map<number, number | null>();

  round16.forEach((match, index) => {
    nextMatchIds.set(match.matchNumber, quarter[Math.floor(index / 2)]?.matchNumber ?? null);
  });
  quarter.forEach((match, index) => {
    nextMatchIds.set(match.matchNumber, semi[Math.floor(index / 2)]?.matchNumber ?? null);
  });
  semi.forEach((match) => {
    nextMatchIds.set(match.matchNumber, final?.matchNumber ?? null);
  });

  return [
    ...round16.map((match) => toBracketMatch(match, 1, nextMatchIds.get(match.matchNumber))),
    ...quarter.map((match) => toBracketMatch(match, 2, nextMatchIds.get(match.matchNumber))),
    ...semi.map((match) => toBracketMatch(match, 3, nextMatchIds.get(match.matchNumber))),
    ...(final ? [toBracketMatch(final, 4, null)] : []),
  ];
}

function toBracketMatch(match: Match, roundNumber: number, nextMatchId: number | null | undefined): BracketMatch {
  const homeScore = match.score?.home;
  const awayScore = match.score?.away;
  const winner = predictedWinnerId(match);

  return {
    id: match.matchNumber,
    round: roundNumber,
    matchNumber: match.matchNumber,
    nextMatchId,
    winner,
    participant1: {
      id: `${match.matchNumber}-home`,
      name: displayTeamName(match.homeTeam),
      score: homeScore,
    },
    participant2: {
      id: `${match.matchNumber}-away`,
      name: displayTeamName(match.awayTeam),
      score: awayScore,
    },
  };
}

function predictedWinnerId(match: Match): string | null {
  if (!hasKnownTeams(match)) {
    return null;
  }

  if (match.aiPrediction.pick === "1") {
    return `${match.matchNumber}-home`;
  }

  if (match.aiPrediction.pick === "2") {
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
