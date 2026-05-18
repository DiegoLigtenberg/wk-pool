import { describe, expect, it } from "vitest";
import { isTournamentView } from "./contract";
import { tournamentFixture } from "../test/tournamentFixture";

describe("isTournamentView", () => {
  it("accepts the tournament payload shape used by the app", () => {
    expect(isTournamentView(tournamentFixture())).toBe(true);
  });

  it("rejects payloads with an invalid summary", () => {
    const payload = tournamentFixture({
      summary: {
        ...tournamentFixture().summary,
        aiAccuracy: Number.NaN,
      },
    });

    expect(isTournamentView(payload)).toBe(false);
  });

  it("rejects matches with invalid prediction values", () => {
    const match = {
      ...tournamentFixture().recentMatches[0],
      aiPrediction: {
        ...tournamentFixture().recentMatches[0].aiPrediction,
        pick: "home",
      },
    };
    const payload = {
      ...tournamentFixture(),
      recentMatches: [match],
    };

    expect(isTournamentView(payload)).toBe(false);
  });
});
