import type { Match } from "../types";

/** Fixed FIFA 2026 knockout tree: winner of match N advances to match M. */
export const KNOCKOUT_NEXT_MATCH: Readonly<Record<number, number>> = {
  73: 90,
  75: 90,
  74: 89,
  77: 89,
  76: 91,
  78: 91,
  79: 92,
  80: 92,
  83: 93,
  84: 93,
  81: 94,
  82: 94,
  86: 95,
  88: 95,
  85: 96,
  87: 96,
  89: 97,
  90: 97,
  93: 98,
  94: 98,
  91: 99,
  92: 99,
  95: 100,
  96: 100,
  97: 101,
  98: 101,
  99: 102,
  100: 102,
  101: 104,
  102: 104,
};

const KNOCKOUT_BRACKET_ROUND: Readonly<Record<string, number>> = {
  "Round of 32": 1,
  "Round of 16": 2,
  "Quarter Finals": 3,
  "Semi Finals": 4,
  Finals: 5,
};

/** Bracket column order so feeder pairs sit together for connector lines. */
const KNOCKOUT_MATCH_ORDER: Readonly<Record<string, readonly number[]>> = {
  "Round of 32": [73, 75, 74, 77, 76, 78, 79, 80, 81, 82, 83, 84, 85, 87, 86, 88],
  "Round of 16": [89, 90, 91, 92, 93, 94, 95, 96],
  "Quarter Finals": [97, 98, 99, 100],
  "Semi Finals": [101, 102],
};

export function knockoutBracketRound(match: Match): number {
  return KNOCKOUT_BRACKET_ROUND[match.round] ?? 1;
}

export function knockoutNextMatchId(matchNumber: number): number | null {
  return KNOCKOUT_NEXT_MATCH[matchNumber] ?? null;
}

export function sortKnockoutRound(matches: Match[], round: string): Match[] {
  const order = KNOCKOUT_MATCH_ORDER[round];
  if (!order) {
    return [...matches].sort((first, second) => first.matchNumber - second.matchNumber);
  }

  const index = new Map(order.map((matchNumber, position) => [matchNumber, position]));
  return [...matches].sort(
    (first, second) =>
      (index.get(first.matchNumber) ?? Number.MAX_SAFE_INTEGER) -
      (index.get(second.matchNumber) ?? Number.MAX_SAFE_INTEGER),
  );
}

export function flattenKnockoutBracket(
  round32: Match[],
  round16: Match[],
  quarter: Match[],
  semi: Match[],
  final?: Match,
): Match[] {
  return [
    ...sortKnockoutRound(round32, "Round of 32"),
    ...sortKnockoutRound(round16, "Round of 16"),
    ...sortKnockoutRound(quarter, "Quarter Finals"),
    ...sortKnockoutRound(semi, "Semi Finals"),
    ...(final ? [final] : []),
  ];
}
