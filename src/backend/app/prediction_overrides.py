"""Handmatige uitzonderingen op modelvoorspellingen (pool / eigen inschatting)."""

from __future__ import annotations

from app.teams import display_team_name, fifa_team_key


def apply_match_overrides(
    *,
    match_number: int | None,
    home_team: str,
    away_team: str,
    stage: str,
    result: dict[str, object],
) -> dict[str, object]:
    if stage != "knockout" or match_number != 75:
        return result
    if fifa_team_key(home_team) != "Netherlands" or fifa_team_key(away_team) != "Morocco":
        return result

    home_nl = display_team_name("Netherlands")
    verdict = f"De AI voorspelt dat {home_nl} wint."
    suggested = {
        "home": 3,
        "away": 2,
        "reason": f"Pool-inschatting: {home_nl} wint na 90 minuten (3-2).",
    }

    updated = dict(result)
    updated["pick"] = "1"
    updated["confidence"] = 52
    updated["homeWinProbability"] = 52
    updated["drawProbability"] = 24
    updated["awayWinProbability"] = 24
    updated["suggestedScore"] = suggested
    updated["explanation"] = verdict

    insight = updated.get("insight")
    if isinstance(insight, dict):
        patched = dict(insight)
        patched["verdict"] = verdict
        updated["insight"] = patched

    return updated
