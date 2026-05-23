"""Find tournament fields that fail the frontend contract (mirrors contract.ts)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()
from typing import Any

PICKS = {"1", "2", "3"}
PREDICTION_STATUSES = {"correct", "wrong", "pending"}
MATCH_STATUSES = {"completed", "upcoming"}
MATCH_STAGES = {"group", "knockout"}


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and value == value  # noqa: PLR0124


def is_record(value: object) -> bool:
    return isinstance(value, dict)


def is_string_array(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def is_score(value: object) -> bool:
    if not is_record(value):
        return False
    return is_number(value.get("home")) and is_number(value.get("away"))


def is_prediction_factor(value: object) -> bool:
    if not is_record(value):
        return False
    scope = value.get("scope")
    return (
        isinstance(value.get("id"), str)
        and is_number(value.get("delta"))
        and isinstance(value.get("label"), str)
        and isinstance(value.get("reason"), str)
        and scope in ("match", "team")
    )


def is_prediction_score_side(value: object) -> bool:
    if not is_record(value):
        return False
    factors = value.get("factors")
    return (
        isinstance(value.get("team"), str)
        and is_number(value.get("powerScore"))
        and is_number(value.get("contextDelta"))
        and is_number(value.get("effectiveScore"))
        and isinstance(factors, list)
        and all(is_prediction_factor(f) for f in factors)
    )


def is_prediction_step(value: object) -> bool:
    if not is_record(value):
        return False
    return isinstance(value.get("title"), str) and isinstance(value.get("body"), str)


def is_prediction_insight(value: object) -> bool:
    if not is_record(value):
        return False
    steps = value.get("steps")
    narrative = value.get("narrative")
    narrative_ok = narrative is None or isinstance(narrative, str)
    steps_ok = steps is None or (isinstance(steps, list) and all(is_prediction_step(step) for step in steps))
    return (
        isinstance(value.get("scoreSummary"), str)
        and isinstance(value.get("verdict"), str)
        and narrative_ok
        and steps_ok
        and is_string_array(value.get("tags"))
        and is_number(value.get("diff"))
        and is_prediction_score_side(value.get("home"))
        and is_prediction_score_side(value.get("away"))
    )


def is_ai_prediction(value: object) -> bool:
    if not is_record(value):
        return False
    confidence = value.get("confidence")
    insight = value.get("insight")
    insight_ok = insight is None if confidence == 0 else is_prediction_insight(insight)
    return (
        value.get("pick") in PICKS
        and is_number(confidence)
        and isinstance(value.get("explanation"), str)
        and value.get("status") in PREDICTION_STATUSES
        and insight_ok
        and (value.get("homeWinProbability") is None or is_number(value.get("homeWinProbability")))
        and (value.get("drawProbability") is None or is_number(value.get("drawProbability")))
        and (value.get("awayWinProbability") is None or is_number(value.get("awayWinProbability")))
    )


def is_match(value: object) -> tuple[bool, str]:
    if not is_record(value):
        return False, "not a record"
    if not is_number(value.get("matchNumber")):
        return False, "matchNumber"
    if not isinstance(value.get("round"), str):
        return False, "round"
    if value.get("stage") not in MATCH_STAGES:
        return False, "stage"
    group = value.get("group")
    if not (isinstance(group, str) or group is None):
        return False, "group"
    for field in ("kickoffAt", "location", "homeTeam", "awayTeam"):
        if not isinstance(value.get(field), str):
            return False, field
    if value.get("status") not in MATCH_STATUSES:
        return False, "status"
    score = value.get("score")
    if score is not None and not is_score(score):
        return False, "score"
    actual = value.get("actualPick")
    if actual is not None and actual not in PICKS:
        return False, "actualPick"
    if not is_ai_prediction(value.get("aiPrediction")):
        return False, "aiPrediction"
    return True, ""


def is_team_insight(value: object) -> tuple[bool, str]:
    if not is_record(value):
        return False, "not a record"
    for field in ("team", "tier", "style", "summary"):
        if not isinstance(value.get(field), str):
            return False, field
    if not is_string_array(value.get("strengths")):
        return False, "strengths"
    if not is_string_array(value.get("risks")):
        return False, "risks"
    niche = value.get("niche")
    if niche is not None and not is_string_array(niche):
        return False, "niche"
    opponents = value.get("opponents")
    if opponents is not None and not is_string_array(opponents):
        return False, "opponents"
    group = value.get("group")
    if group is not None and not isinstance(group, str):
        return False, "group"
    power = value.get("powerScore")
    if power is not None and not is_number(power):
        return False, "powerScore"
    group_context = value.get("groupContext")
    if group_context is not None and not is_string_array(group_context):
        return False, "groupContext"
    spark = value.get("distinctiveSpark")
    if spark is not None and not isinstance(spark, str):
        return False, "distinctiveSpark"
    return True, ""


def is_standing(value: object) -> tuple[bool, str]:
    if not is_record(value):
        return False, "not a record"
    if not isinstance(value.get("team"), str):
        return False, "team"
    for field in ("played", "wins", "draws", "losses", "goalsFor", "goalsAgainst", "goalDifference", "points"):
        if not is_number(value.get(field)):
            return False, field
    return True, ""


def is_summary(value: object) -> tuple[bool, str]:
    if not is_record(value):
        return False, "not a record"
    for field in (
        "totalMatches",
        "groupMatches",
        "completed",
        "upcoming",
        "aiCorrect",
        "aiWrong",
        "aiPending",
        "aiAccuracy",
    ):
        if not is_number(value.get(field)):
            return False, field
    return True, ""


def is_group(value: object) -> tuple[bool, str]:
    if not is_record(value):
        return False, "not a record"
    if not isinstance(value.get("name"), str):
        return False, "name"
    standings = value.get("standings")
    if not isinstance(standings, list):
        return False, "standings"
    for standing in standings:
        ok, reason = is_standing(standing)
        if not ok:
            return False, f"standing:{reason}"
    matches = value.get("matches")
    if not isinstance(matches, list):
        return False, "matches"
    for match in matches:
        ok, reason = is_match(match)
        if not ok:
            return False, f"match:{reason}"
    predicted = value.get("predictedWinner")
    if not isinstance(predicted, str):
        return False, "predictedWinner"
    status = value.get("winnerPredictionStatus")
    if status not in {"correct", "wrong", "pending"}:
        return False, "winnerPredictionStatus"
    return True, ""


def is_tournament_view(tournament: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    ok, reason = is_summary(tournament.get("summary"))
    if not ok:
        errors.append(f"summary: {reason}")

    next_match = tournament.get("nextMatch")
    if next_match is not None:
        ok, reason = is_match(next_match)
        if not ok:
            errors.append(f"nextMatch: {reason}")

    team_insights = tournament.get("teamInsights")
    if not isinstance(team_insights, dict):
        errors.append("teamInsights: missing or not object")
    else:
        for team, insight in team_insights.items():
            ok, reason = is_team_insight(insight)
            if not ok:
                errors.append(f"teamInsights[{team!r}]: {reason}")

    def walk_matches(label: str, matches: list[Any]) -> None:
        for m in matches:
            ok, reason = is_match(m)
            if not ok:
                mn = m.get("matchNumber") if is_record(m) else "?"
                errors.append(f"{label} match {mn}: {reason}")

    walk_matches("recent", tournament.get("recentMatches") or [])
    walk_matches("upcoming", tournament.get("upcomingMatches") or [])
    for g in tournament.get("groups") or []:
        ok, reason = is_group(g)
        if not ok:
            errors.append(f"group {g.get('name') if is_record(g) else '?'}: {reason}")
        elif is_record(g):
            walk_matches(f"group {g.get('name')}", g.get("matches") or [])
    walk_matches("knockout", tournament.get("knockoutMatches") or [])

    ok, reason = is_crystal_ball(tournament.get("crystalBall"))
    if not ok:
        errors.append(f"crystalBall: {reason}")

    return errors


def is_crystal_ball(value: object) -> tuple[bool, str]:
    if not is_record(value):
        return False, "missing or not object"
    group_winners = value.get("groupWinners")
    if not isinstance(group_winners, list):
        return False, "groupWinners"
    for entry in group_winners:
        if not is_record(entry) or not isinstance(entry.get("group"), str) or not isinstance(entry.get("team"), str):
            return False, "groupWinners entry"
        if entry.get("status") not in {"correct", "wrong", "pending"}:
            return False, "groupWinners status"
    projected = value.get("projectedGroups")
    if not isinstance(projected, list):
        return False, "projectedGroups"
    for group in projected:
        ok, reason = is_projected_group(group)
        if not ok:
            return False, f"projectedGroups:{reason}"
    bonus = value.get("bonusQuestions")
    if not isinstance(bonus, list):
        return False, "bonusQuestions"
    for question in bonus:
        if not is_record(question):
            return False, "bonusQuestions entry"
        if not all(isinstance(question.get(key), str) for key in ("id", "label", "value", "helper")):
            return False, "bonusQuestions fields"
    if not is_string_array(value.get("sources")):
        return False, "sources"
    if not isinstance(value.get("contextAsOf"), str):
        return False, "contextAsOf"
    live_stats = value.get("liveStats")
    if not isinstance(live_stats, dict):
        return False, "liveStats"
    if live_stats.get("source") != "api-football":
        return False, "liveStats.source"
    updated_at = live_stats.get("updatedAt")
    if updated_at is not None and not isinstance(updated_at, str):
        return False, "liveStats.updatedAt"
    for key in ("completedMatches", "totalMatches", "yellowCards", "directRedCards"):
        if not isinstance(live_stats.get(key), int):
            return False, f"liveStats.{key}"
    top_scorer = live_stats.get("topScorer")
    if top_scorer is not None:
        if not isinstance(top_scorer, dict):
            return False, "liveStats.topScorer"
        if not isinstance(top_scorer.get("name"), str):
            return False, "liveStats.topScorer.name"
        if not isinstance(top_scorer.get("goals"), int):
            return False, "liveStats.topScorer.goals"
        if not isinstance(top_scorer.get("team"), str):
            return False, "liveStats.topScorer.team"
    return True, ""


def is_projected_group(value: object) -> tuple[bool, str]:
    if not is_record(value):
        return False, "not object"
    if not isinstance(value.get("name"), str):
        return False, "name"
    winner = value.get("winner")
    if winner is not None and not isinstance(winner, str):
        return False, "winner"
    standings = value.get("standings")
    if not isinstance(standings, list):
        return False, "standings"
    for standing in standings:
        ok, reason = is_standing(standing)
        if not ok:
            return False, reason
    return True, ""


def main() -> int:
    if len(sys.argv) > 1:
        tournament = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    else:
        from app.webapp import cached_tournament_view

        cached_tournament_view.cache_clear()
        tournament = cached_tournament_view()

    errors = is_tournament_view(tournament)
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for err in errors[:30]:
            print(err)
        return 1
    print("OK: tournament matches frontend contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
