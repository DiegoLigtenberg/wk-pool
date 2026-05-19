/** Zelfde ladder als backend (`predictions.py` / research-YAML). */

export const TIER_LADDER = [
  "Topfavoriet",
  "Favoriet",
  "Subtopper",
  "Underdog",
  "Verrassingsploeg",
] as const;

export type TierName = (typeof TIER_LADDER)[number];

export function tierRank(tier: string): number | null {
  const index = TIER_LADDER.indexOf(tier as TierName);
  return index === -1 ? null : index + 1;
}
