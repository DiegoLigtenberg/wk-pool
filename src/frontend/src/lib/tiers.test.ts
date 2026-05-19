import { describe, expect, it } from "vitest";
import { TIER_LADDER, tierRank } from "./tiers";

describe("tierRank", () => {
  it("orders subtopper as third tier", () => {
    expect(tierRank("Subtopper")).toBe(3);
    expect(TIER_LADDER).toHaveLength(5);
  });
});
