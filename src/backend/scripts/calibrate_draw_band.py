#!/usr/bin/env python3
"""Hulp: welke |diff|-band levert ~25% gelijk-picks op dit fixture-set?"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.data.teams.context_score import match_context_breakdown
from app.tournament import load_fixtures
from app.teams import fifa_team_key

TARGET_DRAW_PCT = 0.25


def main() -> None:
    rows: list[tuple[int, str, str, int, int, int, int]] = []
    for fx in load_fixtures():
        if not fx.group:
            continue
        br = match_context_breakdown(fifa_team_key(fx.home_team), fifa_team_key(fx.away_team))
        d = int(br["diff"])
        rows.append(
            (
                d,
                fx.home_team,
                fx.away_team,
                int(br["home"]["effectiveScore"]),
                int(br["away"]["effectiveScore"]),
                int(br["home"]["powerScore"]),
                int(br["away"]["powerScore"]),
            )
        )

    n = len(rows)
    print(f"Groepswedstrijden: {n}, streef ~{TARGET_DRAW_PCT:.0%} gelijk\n")
    for t in range(0, 12):
        picks = [r for r in rows if abs(r[0]) <= t]
        print(f"  |diff|<={t:2}: {len(picks):2} ({100*len(picks)/n:.1f}%)")

    best_t = min(range(0, 20), key=lambda t: abs(len([r for r in rows if abs(r[0]) <= t]) / n - TARGET_DRAW_PCT))
    print(f"\nDichtst bij {TARGET_DRAW_PCT:.0%}: |diff|<={best_t} -> {100*len([r for r in rows if abs(r[0]) <= best_t])/n:.1f}%")
    print(f"\nWedstrijden |diff|<={best_t}:")
    for r in sorted(rows, key=lambda x: abs(x[0])):
        if abs(r[0]) <= best_t:
            d, h, a, he, ae, hp, ap = r
            print(f"  diff {d:+3}  {h} vs {a}  eff {he}-{ae}  base {hp}-{ap}")


if __name__ == "__main__":
    main()
