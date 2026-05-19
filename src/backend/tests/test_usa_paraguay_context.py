"""Geen dubbele matchup-bonus op dezelfde 'Zwakwer'-researchregel."""

from app.data.teams.context_score import match_context_breakdown
from app.teams import fifa_team_key


def test_paraguay_does_not_gain_from_usa_self_weakness_note() -> None:
    breakdown = match_context_breakdown(fifa_team_key("USA"), fifa_team_key("Paraguay"))
    usa = breakdown["home"]
    paraguay = breakdown["away"]

    usa_ids = {r["id"] for r in usa["reasons"]}
    paraguay_ids = {r["id"] for r in paraguay["reasons"]}

    assert "tactical_weakness" in usa_ids
    assert "opponent_profile_weak" not in paraguay_ids
    assert paraguay["effectiveScore"] == 72
    assert usa["effectiveScore"] == 82
