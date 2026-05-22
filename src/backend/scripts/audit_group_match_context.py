#!/usr/bin/env python3
"""Dump groepswedstrijden: basis vs host vs research vs totaal. Run vanuit src/backend."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.data.teams.context_score import match_context_breakdown
from app.data.teams.team_loader import get_team_bundle
from app.data.teams.team_registry import HOST_NATIONS
from app.predictions import predict_match
from app.teams import fifa_team_key, display_team_name
from app.tournament import load_fixtures

OUT_PATH = BACKEND / "reports" / "group_match_context_audit.csv"


def _base_pick(home_power: int, away_power: int) -> str:
    if home_power > away_power:
        return "1"
    if away_power > home_power:
        return "2"
    return "3"


def _factor_summary(reasons: list[dict]) -> str:
    parts = []
    for r in reasons:
        d = int(r.get("delta") or 0)
        if d == 0:
            continue
        parts.append(f"{r['id']}:{d:+d}")
    return "; ".join(parts) if parts else "-"


def main() -> None:
    fixtures = [f for f in load_fixtures() if f.group is not None]
    rows: list[dict[str, object]] = []

    for fx in fixtures:
        hk = fifa_team_key(fx.home_team)
        ak = fifa_team_key(fx.away_team)
        br = match_context_breakdown(hk, ak)
        pred = predict_match(fx.home_team, fx.away_team, "group", "1", fx.group or "A")
        hs, aws = br["home"], br["away"]
        hp, ap = int(hs["powerScore"]), int(aws["powerScore"])
        base_diff = hp - ap
        diff = int(br["diff"])
        ctx_swing = diff - base_diff

        base_pick = _base_pick(hp, ap)
        pick = str(pred["pick"])
        pick_flipped = pick != base_pick and not (base_pick == "3" and pick in ("1", "2"))

        rows.append(
            {
                "match_number": fx.match_number,
                "group": fx.group,
                "kickoff": fx.kickoff_at.isoformat(),
                "location": fx.location,
                "home": display_team_name(hk),
                "away": display_team_name(ak),
                "home_power": hp,
                "away_power": ap,
                "base_diff": base_diff,
                "home_host": int(hs.get("hostDelta") or 0),
                "home_travel": int(hs.get("travelDelta") or 0),
                "home_research": int(hs["researchDelta"]),
                "home_context": int(hs["contextDelta"]),
                "home_eff": int(hs["effectiveScore"]),
                "home_factors": _factor_summary(hs["reasons"]),
                "away_host": int(aws.get("hostDelta") or 0),
                "away_travel": int(aws.get("travelDelta") or 0),
                "away_research": int(aws["researchDelta"]),
                "away_context": int(aws["contextDelta"]),
                "away_eff": int(aws["effectiveScore"]),
                "away_factors": _factor_summary(aws["reasons"]),
                "diff": diff,
                "ctx_swing": ctx_swing,
                "pick": pick,
                "base_pick": base_pick,
                "pick_flipped": pick_flipped,
                "home_pct": pred["homeWinProbability"],
                "draw_pct": pred["drawProbability"],
                "away_pct": pred["awayWinProbability"],
                "home_cohost": hk in HOST_NATIONS,
                "away_cohost": ak in HOST_NATIONS,
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT_PATH}")

    # --- Review flags ---
    high_ctx = [r for r in rows if abs(int(r["ctx_swing"])) >= 5]
    flipped = [r for r in rows if r["pick_flipped"]]
    research_cap = [
        r
        for r in rows
        if abs(int(r["home_research"])) >= 4 or abs(int(r["away_research"])) >= 4
    ]
    cohost_duel = [r for r in rows if r["home_cohost"] and r["away_cohost"]]
    tight_ctx_decides = [
        r
        for r in rows
        if abs(int(r["base_diff"])) <= 3 and abs(int(r["ctx_swing"])) >= 3
    ]

    print(f"\nHigh context swing (|ctx_swing|>=5): {len(high_ctx)}")
    for r in high_ctx:
        print(
            f"  #{r['match_number']} {r['home']} vs {r['away']}: "
            f"base_diff={r['base_diff']} ctx_swing={r['ctx_swing']} pick={r['pick']}"
        )

    print(f"\nPick flipped vs base power only: {len(flipped)}")
    for r in flipped:
        print(
            f"  #{r['match_number']} {r['home']} vs {r['away']}: "
            f"base_pick={r['base_pick']} pick={r['pick']} ctx_swing={r['ctx_swing']}"
        )

    print(f"\nResearch at side cap (|r|>=4): {len(research_cap)}")
    for r in research_cap:
        print(f"  #{r['match_number']} {r['home']} vs {r['away']}")

    print(f"\nCo-host vs co-host: {len(cohost_duel)}")
    for r in cohost_duel:
        print(f"  #{r['match_number']} {r['home']} vs {r['away']} diff={r['diff']}")

    print(f"\nTight base but context >=3 swing: {len(tight_ctx_decides)}")
    for r in tight_ctx_decides:
        print(
            f"  #{r['match_number']} {r['home']} vs {r['away']}: "
            f"base={r['base_diff']} swing={r['ctx_swing']}"
        )


if __name__ == "__main__":
    main()
