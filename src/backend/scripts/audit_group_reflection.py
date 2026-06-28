"""Deep audit: picks, draws, goals — predictions vs synced group results."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.match_results_store import load_results, result_for_match
from app.predictions import predict_match
from app.teams import display_team_name
from app.tournament import load_fixtures

OUT = Path(__file__).resolve().parent / "audit_group_reflection.json"


def actual_pick(h: int, a: int) -> str:
    if h > a:
        return "1"
    if h < a:
        return "2"
    return "3"


def main() -> int:
    store = load_results()
    rows: list[dict[str, object]] = []

    pred_draw = actual_draw = 0
    pred_draw_correct = 0
    pred_win_wrong_as_draw = 0
    pred_win_wrong_missed_draw = 0
    goal_errors_when_wrong: list[int] = []

    for fx in load_fixtures():
        if not fx.group:
            continue
        stored = result_for_match(store, fx.match_number)
        if not stored:
            continue
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
        total_goals = h + a

        if pick == "3":
            pred_draw += 1
        if actual == "3":
            actual_draw += 1
        if pick == "3" and actual == "3":
            pred_draw_correct += 1
        if pick == "3" and actual != "3":
            pred_win_wrong_as_draw += 1
        if pick != "3" and actual == "3":
            pred_win_wrong_missed_draw += 1
        if pick != actual:
            goal_errors_when_wrong.append(total_goals)

        rows.append(
            {
                "match": f"{display_team_name(fx.home_team)} – {display_team_name(fx.away_team)}",
                "score": f"{h}-{a}",
                "goals": total_goals,
                "pick": pick,
                "actual": actual,
                "ok": pick == actual,
            }
        )

    wrong = [r for r in rows if not r["ok"]]
    low_scoring_draws = [
        r for r in rows if r["actual"] == "3" and int(str(r["score"]).split("-")[0]) + int(str(r["score"]).split("-")[1]) <= 2
    ]
    high_scoring = [r for r in rows if r["goals"] >= 5]

    # knockout R32 now
    from app.tournament import build_tournament_view

    t = build_tournament_view()
    r32 = [m for m in t["knockoutMatches"] if m["round"] == "Round of 32"]
    r32_draws = [m for m in r32 if m["aiPrediction"]["pick"] == "3"]
    r32_scores = [
        {
            "match": f"{m['homeTeam']} – {m['awayTeam']}",
            "pick": m["aiPrediction"]["pick"],
            "score": m["aiPrediction"].get("suggestedScore"),
        }
        for m in r32
    ]

    summary = {
        "group": {
            "matches": len(rows),
            "pick_accuracy_pct": round(100 * sum(1 for r in rows if r["ok"]) / len(rows), 1),
            "predicted_draws": pred_draw,
            "actual_draws": actual_draw,
            "draw_predictions_correct": pred_draw_correct,
            "predicted_draw_but_winner": pred_win_wrong_as_draw,
            "predicted_winner_but_draw": pred_win_wrong_missed_draw,
            "avg_goals_when_pick_wrong": round(sum(goal_errors_when_wrong) / len(goal_errors_when_wrong), 2)
            if goal_errors_when_wrong
            else 0,
            "low_scoring_actual_draws_0_2_goals": len(low_scoring_draws),
            "high_scoring_matches_5plus": len(high_scoring),
        },
        "r32": {
            "matches": len(r32),
            "draw_picks": len(r32_draws),
            "draw_pick_pct": round(100 * len(r32_draws) / len(r32), 1) if r32 else 0,
            "draw_matches": [
                {
                    "match": f"{m['homeTeam']} – {m['awayTeam']}",
                    "suggested": m["aiPrediction"].get("suggestedScore"),
                }
                for m in r32_draws
            ],
        },
        "reflection": {
            "draw_model_group": (
                f"Gelijk {pred_draw}x voorspeld vs {actual_draw}x echt; "
                f"maar slechts {pred_draw_correct}x goed — "
                f"{pred_win_wrong_as_draw}x onterecht gelijk, {pred_win_wrong_missed_draw}x gelijk gemist."
            ),
            "r32_draw_rate": (
                f"{len(r32_draws)}/16 R32 = {round(100*len(r32_draws)/16,1)}% gelijk-pick "
                f"(groepsfase echt ~{round(100*actual_draw/len(rows),1)}%)."
            ),
        },
    }

    OUT.write_text(json.dumps({"summary": summary, "wrong": wrong, "r32": r32_scores}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
