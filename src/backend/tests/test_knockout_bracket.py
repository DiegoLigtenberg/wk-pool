"""Knockout bracket resolution and poule-momentum predictions."""

from app.group_form import GroupFormStats, build_group_form_index
from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.predictions import is_known_team, predict_match
from app.tournament import build_tournament_view, load_fixtures


def _full_group_results() -> dict[str, object]:
    """Minimal store: every group match finished 1-0 for the home side."""
    matches: dict[str, object] = {}
    for fixture in load_fixtures():
        if fixture.group is None:
            continue
        matches[str(fixture.match_number)] = {"score": {"home": 1, "away": 0}}
    return {"version": 1, "matches": matches, "tournamentTotals": {"yellowCards": 0, "directRedCards": 0}}


def test_r32_slots_resolve_to_real_teams() -> None:
    fixtures = load_fixtures()
    store = _full_group_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    assert bracket is not None

    r32 = [fx for fx in fixtures if fx.round_number == "Round of 32"]
    assert len(r32) == 16

    for fixture in r32:
        home, away = resolve_knockout_teams(fixture, bracket)
        assert is_known_team(home), f"match {fixture.match_number} home={home!r}"
        assert is_known_team(away), f"match {fixture.match_number} away={away!r}"


def test_knockout_prediction_uses_group_momentum() -> None:
    home = GroupFormStats(
        fifa_team="Mexico",
        group="A",
        rank=1,
        points=9,
        played=3,
        wins=3,
        draws=0,
        losses=0,
        goals_for=8,
        goals_against=2,
        goal_difference=6,
    )
    away = GroupFormStats(
        fifa_team="South Africa",
        group="A",
        rank=2,
        points=4,
        played=3,
        wins=1,
        draws=1,
        losses=1,
        goals_for=3,
        goals_against=4,
        goal_difference=-1,
    )
    pred = predict_match(
        "Mexico",
        "South Africa",
        "knockout",
        "Round of 32",
        None,
        group_forms=(home, away),
    )
    kinds = {a.get("kind") for a in pred["insight"].get("poolAdjustments", [])}
    assert "live_form" in kinds or "standings" in kinds or "momentum" in kinds
    assert pred["confidence"] > 0


def test_tournament_view_r32_has_predictions_when_results_complete(monkeypatch) -> None:
    store = _full_group_results()

    def _fake_load() -> dict[str, object]:
        return store

    monkeypatch.setattr("app.tournament.load_results", _fake_load)
    tournament = build_tournament_view()
    r32 = [m for m in tournament["knockoutMatches"] if m["round"] == "Round of 32"]
    assert len(r32) == 16
    for match in r32:
        assert match["aiPrediction"]["confidence"] > 0
        assert "wacht" not in str(match["aiPrediction"].get("explanation", "")).lower()


def test_form_index_matches_standings_order() -> None:
    store = _full_group_results()
    index = build_group_form_index(load_fixtures(), store)
    group_a = [s for s in index.values() if s.group == "A"]
    assert len(group_a) == 4
    ranks = sorted(s.rank for s in group_a)
    assert ranks == [1, 2, 3, 4]
