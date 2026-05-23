"""Crystal Ball: groepswinnaars uit AI-picks + bonus uit research-YAML."""

from __future__ import annotations

from app.crystal_ball_research import load_crystal_ball_research
from app.tournament import _standings


def _score_from_pick(pick: str) -> tuple[int, int]:
    if pick == "1":
        return (1, 0)
    if pick == "2":
        return (0, 1)
    return (1, 1)


def build_crystal_ball_view(
    group_stage_matches: list[dict[str, object]],
    *,
    results_store: dict[str, object] | None = None,
    completed_count: int = 0,
    total_count: int = 0,
) -> dict[str, object]:
    research = load_crystal_ball_research()
    projected_groups = _projected_group_views(group_stage_matches)
    group_winners = [
        {"group": group["name"], "team": group["winner"]}
        for group in projected_groups
        if group.get("winner")
    ]
    totals = results_store.get("tournamentTotals", {}) if results_store else {}
    if not isinstance(totals, dict):
        totals = {}
    top_scorer = results_store.get("topScorer") if results_store else None
    if not isinstance(top_scorer, dict):
        top_scorer = None

    return {
        "groupWinners": group_winners,
        "projectedGroups": projected_groups,
        "bonusQuestions": research["bonusQuestions"],
        "sources": research["sources"],
        "contextAsOf": research["contextAsOf"],
        "liveStats": {
            "source": "api-football",
            "updatedAt": results_store.get("updatedAt") if results_store else None,
            "completedMatches": completed_count,
            "totalMatches": total_count,
            "yellowCards": int(totals.get("yellowCards", 0)),
            "directRedCards": int(totals.get("directRedCards", 0)),
            "topScorer": top_scorer,
        },
    }


def _projected_group_views(
    group_stage_matches: list[dict[str, object]],
) -> list[dict[str, object]]:
    group_names = sorted({match["group"] for match in group_stage_matches if match["group"]})
    groups: list[dict[str, object]] = []

    for group_name in group_names:
        group_matches = [match for match in group_stage_matches if match["group"] == group_name]
        standings = _standings(group_matches, from_picks=True)
        winner = str(standings[0]["team"]) if standings else None
        groups.append(
            {
                "name": group_name,
                "winner": winner,
                "standings": standings,
            }
        )

    return groups
