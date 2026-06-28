"""Voorgestelde uitslag (doelpunten) bij pool-pick 1/2/3."""

from __future__ import annotations


def suggest_match_score(
    *,
    pick: str,
    adjusted_diff: int,
    stage: str,
    home_goals_per_game: float = 0.0,
    away_goals_per_game: float = 0.0,
) -> dict[str, int | str]:
    """Illustratieve score na 90 minuten, afgestemd op pick en diff."""
    diff = abs(int(adjusted_diff))
    combined_attack = home_goals_per_game + away_goals_per_game

    if pick == "3":
        if combined_attack >= 3.2:
            home, away = 2, 2
            reason = "Beide teams scoorden regelmatig in de poule; 2-2 na 90 min is plausibel."
        elif combined_attack >= 2.2:
            home, away = 1, 1
            reason = "Evenwichtig duel met aanvallend vermogen; gelijk na 90 min (1-1)."
        else:
            home, away = 0, 0
            reason = "Krappe balans en voorzichtige poules; 0-0 na 90 min past bij dit beeld."
        return {"home": home, "away": away, "reason": reason}

    if pick == "1":
        if diff >= 14:
            home, away = 3, 0
        elif diff >= 10:
            home, away = 3, 1
        elif diff >= 7:
            home, away = 2, 0
        elif diff >= 4:
            home, away = 2, 1
        else:
            home, away = 1, 0
        reason = _winner_score_reason(home, away, side="thuis", diff=diff, stage=stage)
        return {"home": home, "away": away, "reason": reason}

    if diff >= 14:
        home, away = 0, 3
    elif diff >= 10:
        home, away = 1, 3
    elif diff >= 7:
        home, away = 0, 2
    elif diff >= 4:
        home, away = 1, 2
    else:
        home, away = 0, 1
    reason = _winner_score_reason(home, away, side="uit", diff=diff, stage=stage)
    return {"home": home, "away": away, "reason": reason}


def _winner_score_reason(home: int, away: int, *, side: str, diff: int, stage: str) -> str:
    margin = abs(home - away)
    if stage == "knockout":
        phase = "na 90 minuten"
    else:
        phase = "in de poule"
    if margin >= 3:
        return f"Duidelijke favoriet ({diff} punten verschil in het model); {home}-{away} {phase}."
    if margin == 2:
        return f"Overtuigende winst voor {side}; {home}-{away} {phase}."
    return f"Krappe winst voor {side}; {home}-{away} {phase}."
