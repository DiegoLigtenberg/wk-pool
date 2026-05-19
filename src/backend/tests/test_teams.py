"""Nederlandse landnamen en FIFA-sleutel."""

from app.predictions import TEAM_PROFILES
from app.teams import TEAM_NAMES_NL, display_team_name, fifa_team_key, localize_teams_in_text


def test_every_profile_has_dutch_name() -> None:
    missing = sorted(team for team in TEAM_PROFILES if team not in TEAM_NAMES_NL)
    assert missing == []


def test_fifa_and_dutch_roundtrip() -> None:
    for fifa, nl in TEAM_NAMES_NL.items():
        assert display_team_name(fifa) == nl
        assert fifa_team_key(nl) == fifa


def test_localize_teams_in_text() -> None:
    text = "Groep met Netherlands, Côte d'Ivoire en Korea Republic."
    assert "Nederland" in localize_teams_in_text(text)
    assert "Ivoorkust" in localize_teams_in_text(text)
    assert "Zuid-Korea" in localize_teams_in_text(text)
    assert "Netherlands" not in localize_teams_in_text(text)
