"""Compare group-stage AI picks to synced results."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.data.teams.context_score import match_context_breakdown
from app.match_results_store import load_results, result_for_match
from app.predictions import predict_match
from app.teams import display_team_name, fifa_team_key
from app.tournament import load_fixtures

OUT = Path(__file__).resolve().parent / "audit_group_accuracy.json"


def actual_pick(home: int, away: int) -> str:
    if home > away:
        return "1"
    if home < away:
        return "2"
    return "3"


def main() -> int:
    store = load_results()
    wrong: list[dict[str, object]] = []
    team_stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pred_w": 0, "pred_l": 0, "actual_pts": 0, "expected_rank_pts": 0}
    )

    total = 0
    for fx in load_fixtures():
        if not fx.group:
            continue
        stored = result_for_match(store, fx.match_number)
        if not stored:
            continue
        total += 1
        h = int(stored["score"]["home"])
        a = int(stored["score"]["away"])
        actual = actual_pick(h, a)
        pred = predict_match(
            fx.home_team,
            fx.away_team,
            "group",
            fx.round_number,
            fx.group,
            match_number=fx.match_number,
        )
        pick = str(pred["pick"])
        home_key = fifa_team_key(fx.home_team)
        away_key = fifa_team_key(fx.away_team)
        br = match_context_breakdown(home_key, away_key)
        diff = int(br["diff"])

        if pick != actual:
            wrong.append(
                {
                    "matchNumber": fx.match_number,
                    "match": f"{display_team_name(home_key)} – {display_team_name(away_key)}",
                    "score": f"{h}-{a}",
                    "predicted": pick,
                    "actual": actual,
                    "diff": diff,
                }
            )

        for team, got_w in ((home_key, pick == "1"), (away_key, pick == "2")):
            if got_w:
                team_stats[team]["pred_w"] += 1
            else:
                team_stats[team]["pred_l"] += 1

    # group form vs pre-tournament power (rough surprise)
    from app.group_form import build_group_form_index
    from app.data.teams.team_loader import get_team_bundle

    form = build_group_form_index(load_fixtures(), store)
    surprises: list[dict[str, object]] = []
    for team, stats in sorted(form.items(), key=lambda x: display_team_name(x[0])):
        bundle = get_team_bundle(team)
        power = int(bundle.power_score) if bundle else 70
        if power >= 82:
            expected_pts = 7
        elif power >= 74:
            expected_pts = 5
        elif power >= 68:
            expected_pts = 4
        else:
            expected_pts = 2
        delta = stats.points - expected_pts
        if abs(delta) >= 2:
            surprises.append(
                {
                    "team": display_team_name(team),
                    "power": power,
                    "points": stats.points,
                    "expected": expected_pts,
                    "delta": delta,
                    "rank": stats.rank,
                    "gd": stats.goal_difference,
                }
            )

    summary = {
        "matches_with_results": total,
        "wrong_picks": len(wrong),
        "accuracy_pct": round(100 * (total - len(wrong)) / total, 1) if total else 0,
        "draw_actual": sum(1 for fx in load_fixtures() if fx.group and result_for_match(store, fx.match_number) and int(result_for_match(store, fx.match_number)["score"]["home"]) == int(result_for_match(store, fx.match_number)["score"]["away"])),
    }
    OUT.write_text(
        json.dumps({"summary": summary, "wrong": wrong, "surprises": surprises}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nWrong ({len(wrong)}):")
    for row in wrong:
        print(f"  {row['match']} {row['score']} pred={row['predicted']} actual={row['actual']} diff={row['diff']:+d}")
    print(f"\nSurprises ({len(surprises)}):")
    for row in surprises:
        sign = "+" if row["delta"] > 0 else ""
        print(f"  {row['team']}: {row['points']}p (exp ~{row['expected']}) {sign}{row['delta']} rank {row['rank']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
