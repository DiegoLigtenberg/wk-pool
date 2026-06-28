import { describe, expect, it } from "vitest";
import { flattenKnockoutBracket, knockoutNextMatchId, sortKnockoutRound } from "./knockoutBracket";
import type { Match } from "../types";

function stubMatch(matchNumber: number, round: string): Match {
  return {
    matchNumber,
    round,
    stage: "knockout",
    group: null,
    kickoffAt: "2026-07-01T12:00:00Z",
    location: "Test",
    homeTeam: "Home",
    awayTeam: "Away",
    status: "upcoming",
    score: null,
    actualPick: null,
    aiPrediction: {
      pick: "1",
      confidence: 50,
      status: "pending",
      probabilities: { home: 50, draw: 25, away: 25 },
      drawProbability: null,
      suggestedScore: null,
      insight: null,
    },
  };
}

describe("knockoutBracket", () => {
  it("maps round of 32 winners into the fixed fifa tree", () => {
    expect(knockoutNextMatchId(73)).toBe(90);
    expect(knockoutNextMatchId(75)).toBe(90);
    expect(knockoutNextMatchId(74)).toBe(89);
    expect(knockoutNextMatchId(85)).toBe(96);
    expect(knockoutNextMatchId(104)).toBeNull();
  });

  it("orders bracket columns with feeder pairs together", () => {
    const round32 = [73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88].map((matchNumber) =>
      stubMatch(matchNumber, "Round of 32"),
    );

    expect(sortKnockoutRound(round32, "Round of 32").map((match) => match.matchNumber)).toEqual([
      73, 75, 74, 77, 76, 78, 79, 80, 81, 82, 83, 84, 85, 87, 86, 88,
    ]);
  });

  it("flattens all knockout rounds for the bracket component", () => {
    const round32 = [73, 88].map((matchNumber) => stubMatch(matchNumber, "Round of 32"));
    const round16 = [89, 96].map((matchNumber) => stubMatch(matchNumber, "Round of 16"));
    const quarter = [97, 100].map((matchNumber) => stubMatch(matchNumber, "Quarter Finals"));
    const semi = [101, 102].map((matchNumber) => stubMatch(matchNumber, "Semi Finals"));
    const final = stubMatch(104, "Finals");

    expect(flattenKnockoutBracket(round32, round16, quarter, semi, final).map((match) => match.matchNumber)).toEqual([
      73, 88, 89, 96, 97, 100, 101, 102, 104,
    ]);
  });
});
