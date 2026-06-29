"""Knock-out sync uses resolved team names, not CSV placeholders."""

from datetime import datetime, timezone

from app.football_sync import sync_teams_for_fixture
from app.knockout_bracket import build_knockout_bracket_state
from app.match_results_store import load_results
from app.tournament import load_fixtures


def _full_group_results() -> dict[str, object]:
    matches: dict[str, object] = {}
    for fixture in load_fixtures():
        if fixture.group is None:
            continue
        matches[str(fixture.match_number)] = {"score": {"home": 1, "away": 0}}
    return {"version": 1, "matches": matches, "tournamentTotals": {"yellowCards": 0, "directRedCards": 0}}


def test_knockout_resolves_teams_not_csv_placeholders() -> None:
    fixtures = load_fixtures()
    r32 = next(fx for fx in fixtures if fx.match_number == 73)
    assert r32.home_team == "2A"

    bracket = build_knockout_bracket_state(fixtures, _full_group_results())
    assert bracket is not None
    teams = sync_teams_for_fixture(r32, bracket=bracket)
    assert teams is not None
    home, away = teams
    assert home != "2A" and away != "2B"


def test_knockout_resolves_real_teams_when_group_complete() -> None:
    store = load_results()
    fixtures = load_fixtures()
    bracket = build_knockout_bracket_state(fixtures, store)
    assert bracket is not None

    r32 = next(fx for fx in fixtures if fx.match_number == 73)
    teams = sync_teams_for_fixture(r32, bracket=bracket)
    assert teams is not None
    home, away = teams
    assert home not in {"2A", "2B", "To be announced"}
    assert away not in {"2A", "2B", "To be announced"}


def test_group_fixture_uses_csv_teams() -> None:
    fixture = next(fx for fx in load_fixtures() if fx.match_number == 1)
    teams = sync_teams_for_fixture(fixture, bracket=None)
    assert teams == (fixture.home_team, fixture.away_team)
