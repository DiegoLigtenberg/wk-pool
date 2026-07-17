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
    if stage != "knockout" or match_number is None:
        return result

    if match_number == 75:
        return _netherlands_morocco_override(home_team, away_team, result)
    if match_number == 103:
        return _third_place_france_england_override(home_team, away_team, result)
    if match_number == 104:
        return _final_spain_argentina_override(home_team, away_team, result)
    return result


def _netherlands_morocco_override(
    home_team: str,
    away_team: str,
    result: dict[str, object],
) -> dict[str, object]:
    if fifa_team_key(home_team) != "Netherlands" or fifa_team_key(away_team) != "Morocco":
        return result

    home_nl = display_team_name("Netherlands")
    return _apply_ai_style_override(
        result,
        pick="1",
        home_goals=3,
        away_goals=2,
        winner_nl=home_nl,
        confidence=52,
        home_win=52,
        draw=24,
        away_win=24,
        reason=f"Pool-inschatting: {home_nl} wint na 90 minuten (3-2).",
    )


def _third_place_france_england_override(
    home_team: str,
    away_team: str,
    result: dict[str, object],
) -> dict[str, object]:
    home_key = fifa_team_key(home_team)
    away_key = fifa_team_key(away_team)
    if {home_key, away_key} != {"France", "England"}:
        return result

    france_nl = display_team_name("France")
    if home_key == "France":
        pick, home_goals, away_goals = "1", 2, 1
        home_win, draw, away_win = 58, 22, 20
    else:
        pick, home_goals, away_goals = "2", 1, 2
        home_win, draw, away_win = 20, 22, 58

    return _apply_ai_style_override(
        result,
        pick=pick,
        home_goals=home_goals,
        away_goals=away_goals,
        winner_nl=france_nl,
        confidence=58,
        home_win=home_win,
        draw=draw,
        away_win=away_win,
        reason=(
            f"Beide teams vielen net buiten de finale; na 90 minuten ziet de AI "
            f"{france_nl} als knappe winnaar ({home_goals}-{away_goals})."
        ),
    )


def _final_spain_argentina_override(
    home_team: str,
    away_team: str,
    result: dict[str, object],
) -> dict[str, object]:
    home_key = fifa_team_key(home_team)
    away_key = fifa_team_key(away_team)
    if {home_key, away_key} != {"Spain", "Argentina"}:
        return result

    spain_nl = display_team_name("Spain")
    if home_key == "Spain":
        pick, home_goals, away_goals = "1", 3, 2
        home_win, draw, away_win = 54, 20, 26
    else:
        pick, home_goals, away_goals = "2", 2, 3
        home_win, draw, away_win = 26, 20, 54

    return _apply_ai_style_override(
        result,
        pick=pick,
        home_goals=home_goals,
        away_goals=away_goals,
        winner_nl=spain_nl,
        confidence=54,
        home_win=home_win,
        draw=draw,
        away_win=away_win,
        reason=(
            f"Finale op 90 minuten: de AI verwacht een open duel waarin "
            f"{spain_nl} net doorzet ({home_goals}-{away_goals})."
        ),
    )


def _apply_ai_style_override(
    result: dict[str, object],
    *,
    pick: str,
    home_goals: int,
    away_goals: int,
    winner_nl: str,
    confidence: int,
    home_win: int,
    draw: int,
    away_win: int,
    reason: str,
) -> dict[str, object]:
    verdict = f"De AI voorspelt dat {winner_nl} wint."
    suggested = {
        "home": home_goals,
        "away": away_goals,
        "reason": reason,
    }

    updated = dict(result)
    updated["pick"] = pick
    updated["confidence"] = confidence
    updated["homeWinProbability"] = home_win
    updated["drawProbability"] = draw
    updated["awayWinProbability"] = away_win
    updated["suggestedScore"] = suggested
    updated["explanation"] = verdict

    insight = updated.get("insight")
    if isinstance(insight, dict):
        patched = dict(insight)
        patched["verdict"] = verdict
        updated["insight"] = patched

    return updated
