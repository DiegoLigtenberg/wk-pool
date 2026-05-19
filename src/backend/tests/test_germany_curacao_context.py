"""Duitsland–Curaçao: geen gespiegelde compact-blok regels."""

from app.data.teams.context_score import match_context_breakdown
from app.display_text import humanize_factor_reason
from app.teams import fifa_team_key


def test_germany_curacao_no_mirror_compact_block() -> None:
    br = match_context_breakdown(fifa_team_key("Germany"), fifa_team_key("Curaçao"))
    home, away = br["home"], br["away"]
    home_text = " ".join(r["reason"] for r in home["reasons"]).lower()
    away_text = " ".join(r["reason"] for r in away["reasons"]).lower()

    assert "opponent_profile_strong" not in {r["id"] for r in home["reasons"]}
    assert "tactical_strength" in {r["id"] for r in away["reasons"]}
    assert "extra aandacht van curaçao" not in away_text
    assert "in dit duel speelt mee" not in home_text
    assert home_text.count("compact") <= 1
    assert away_text.count("compact") <= 1


def test_opener_lines_are_readable() -> None:
    edge = humanize_factor_reason(
        "Curaçao leunt in dit duel op opener; dat vraagt een gericht plan van Duitsland.",
        factor_id="matchup_edge",
        subject_team="Duitsland",
        opponent_team="Curaçao",
    )
    psych = humanize_factor_reason(
        "Duitsland opener intimiderend.",
        factor_id="psychology",
        subject_team="Curaçao",
        opponent_team="Duitsland",
    )
    assert "WK-debuut" in edge or "groepsopener" in edge.lower()
    assert "leunt" not in edge.lower()
    assert "intimiderend" not in psych.lower() or "favoriet" in psych.lower()
