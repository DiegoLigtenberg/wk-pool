import type { Group, Match, SelectOption, TournamentView } from "../types";
import { teamNameNl, isRealTeamName } from "./teams";

export const STATUS_FILTER_OPTIONS: SelectOption[] = [
  { value: "all", label: "Alle wedstrijden" },
  { value: "completed", label: "Gespeeld" },
  { value: "upcoming", label: "Nog te spelen" },
];

export function groupMatches(tournament: TournamentView): Match[] {
  return tournament.groups
    .flatMap((group) => group.matches)
    .sort(byKickoff);
}

export function allMatches(tournament: TournamentView): Match[] {
  return [...groupMatches(tournament), ...tournament.knockoutMatches].sort(byKickoff);
}

export function teamSelectOptions(matches: Match[]): SelectOption[] {
  const teams = Array.from(new Set(matches.flatMap((match) => [match.homeTeam, match.awayTeam])))
    .filter(isRealTeamName)
    .sort((first, second) => teamNameNl(first).localeCompare(teamNameNl(second), "nl-NL"));

  return [
    { value: "", label: "Alle landen" },
    ...teams.map((team) => ({ value: team, label: teamNameNl(team) })),
  ];
}

export function phaseSelectOptions(matches: Match[]): SelectOption[] {
  const groups = Array.from(
    new Set(
      matches
        .filter((match) => match.stage === "group" && match.group)
        .map((match) => match.group as string),
    ),
  ).sort((first, second) => first.localeCompare(second, "nl-NL", { numeric: true }));

  const hasKnockoutMatches = matches.some((match) => match.stage === "knockout");

  return [
    { value: "all", label: "Alle fases" },
    ...groups.map((group) => ({ value: `group:${group}`, label: `Poule ${group}` })),
    ...(hasKnockoutMatches ? [{ value: "knockout", label: "Knock-out" }] : []),
  ];
}

export function groupStageSummary(groups: Group[]) {
  const matches = groups.flatMap((group) => group.matches);
  return {
    played: matches.filter((match) => match.status === "completed").length,
    total: matches.length,
  };
}

function byKickoff(first: Match, second: Match): number {
  return new Date(first.kickoffAt).getTime() - new Date(second.kickoffAt).getTime();
}
