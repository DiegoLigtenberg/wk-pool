"""Geen gespiegelde +/- en dubbele Isidor/compact-lijnen Haïti–Schotland."""

from app.data.teams.context_score import match_context_breakdown
from app.display_text import humanize_factor_reason
from app.teams import fifa_team_key


def test_haiti_scotland_no_mirror_style_and_isidor_dupes() -> None:
    br = match_context_breakdown(fifa_team_key("Haiti"), fifa_team_key("Scotland"))
    home, away = br["home"], br["away"]

    home_ids = {r["id"] for r in home["reasons"]}
    away_ids = {r["id"] for r in away["reasons"]}

    assert "matchup_risk" not in home_ids
    assert "matchup_edge" not in away_ids
    assert sum(1 for r in away["reasons"] if r["id"] == "style_matchup" and r["delta"] < 0) == 0

    home_text = " ".join(r["reason"] for r in home["reasons"]).lower()
    assert "isidor" in home_text
    assert "bellegarde" in home_text
    assert "sunderland" in home_text
    assert home_text.count("isidor") == 1


def test_clarke_compact_humanized_when_present() -> None:
    text = humanize_factor_reason(
        "Scotland Clarke compact.",
        factor_id="matchup_risk",
        subject_team="Haïti",
        opponent_team="Schotland",
    )
    assert "Steve Clarke" in text
    assert "compact" in text.lower()
    assert "Haïti" in text
