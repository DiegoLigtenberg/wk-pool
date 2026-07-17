"""Tests for knock-out round momentum in pool_edge."""

from app.knockout_form import KnockoutRoundStats
from app.pool_edge import apply_adjustments, knockout_momentum_adjustments
from app.predictions import predict_match
from app.group_form import build_group_form_index
from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.knockout_form import build_knockout_round_form_index
from app.match_results_store import load_results
from app.tournament import load_fixtures


def test_knockout_upset_and_favorite_trim() -> None:
    norway_ko = KnockoutRoundStats(
        played=2,
        wins=2,
        draws=0,
        losses=0,
        goals_for=4,
        goals_against=2,
        upset_wins=1,
        max_upset_power_gap=14,
    )
    england_ko = KnockoutRoundStats(
        played=2,
        wins=2,
        draws=0,
        losses=0,
        goals_for=5,
        goals_against=3,
        upset_wins=0,
        max_upset_power_gap=0,
    )
    adj = knockout_momentum_adjustments(
        norway_ko,
        england_ko,
        home_key="Norway",
        away_key="England",
        base_diff=-16,
    )
    kinds = {a.kind for a in adj}
    assert "knockout_form" in kinds
    adjusted = apply_adjustments(-16, adj)
    assert adjusted > -16


def test_knockout_attack_boost_for_high_scoring_team() -> None:
    belgium_ko = KnockoutRoundStats(
        played=2,
        wins=2,
        draws=0,
        losses=0,
        goals_for=7,
        goals_against=3,
        upset_wins=0,
        max_upset_power_gap=0,
    )
    adj = knockout_momentum_adjustments(
        None,
        belgium_ko,
        home_key="Spain",
        away_key="Belgium",
        base_diff=4,
    )
    assert any(a.id == "away_ko_attack" for a in adj)


def test_qf_norway_england_less_overconfident_than_before() -> None:
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    assert bracket is not None
    form = build_group_form_index(fixtures, store)
    ko = build_knockout_round_form_index(
        fixtures, store, bracket.resolved_teams, before_round="Quarter Finals"
    )
    fx = next(f for f in fixtures if f.match_number == 99)
    home, away = resolve_knockout_teams(fx, bracket)
    pred = predict_match(
        home,
        away,
        "knockout",
        fx.round_number,
        None,
        match_number=fx.match_number,
        group_forms=(form.get(home), form.get(away)),
        knockout_forms=(ko.get(home), ko.get(away)),
    )
    labels = [str(a.get("label", "")) for a in pred["insight"].get("poolAdjustments", [])]
    assert any("KO" in label for label in labels)
    assert int(pred["awayWinProbability"]) <= 78


def test_qf_argentina_switzerland_includes_defensive_ko_nudge() -> None:
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    assert bracket is not None
    form = build_group_form_index(fixtures, store)
    ko = build_knockout_round_form_index(
        fixtures, store, bracket.resolved_teams, before_round="Quarter Finals"
    )
    fx = next(f for f in fixtures if f.match_number == 100)
    home, away = resolve_knockout_teams(fx, bracket)
    pred = predict_match(
        home,
        away,
        "knockout",
        fx.round_number,
        None,
        match_number=fx.match_number,
        group_forms=(form.get(home), form.get(away)),
        knockout_forms=(ko.get(home), ko.get(away)),
    )
    ids = [str(a.get("id", "")) for a in pred["insight"].get("poolAdjustments", [])]
    assert "ko_defensive_underdog_away" in ids or int(pred["drawProbability"]) >= 12


def test_spain_belgium_qf_retro_pick_winner_not_draw() -> None:
    """QF les: Spanje thuis vs hete België — winnaar i.p.v. gelijk."""
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    form = build_group_form_index(fixtures, store)
    ko = build_knockout_round_form_index(
        fixtures, store, bracket.resolved_teams, before_round="Quarter Finals"
    )
    fx = next(f for f in fixtures if f.match_number == 98)
    home, away = resolve_knockout_teams(fx, bracket)
    pred = predict_match(
        home,
        away,
        "knockout",
        fx.round_number,
        None,
        match_number=98,
        group_forms=(form.get(home), form.get(away)),
        knockout_forms=(ko.get(home), ko.get(away)),
    )
    assert pred["pick"] == "1"


def test_semi_finals_resolve_with_predictions() -> None:
    from app.tournament import build_tournament_view

    tournament = build_tournament_view()
    sf = [m for m in tournament["knockoutMatches"] if m["round"] == "Semi Finals"]
    assert len(sf) == 2
    for match in sf:
        assert "To be announced" not in match["homeTeam"]
        assert match["aiPrediction"]["confidence"] > 0
        assert match["aiPrediction"].get("suggestedScore") is not None
    assert {m["matchNumber"] for m in sf} == {101, 102}


def test_finals_and_third_place_resolve_with_overrides() -> None:
    from app.tournament import build_tournament_view

    tournament = build_tournament_view()
    finals = [m for m in tournament["knockoutMatches"] if m["round"] == "Finals"]
    by_number = {m["matchNumber"]: m for m in finals}

    third = by_number[103]
    assert {"Frankrijk", "Engeland"} == {third["homeTeam"], third["awayTeam"]}
    sug3 = third["aiPrediction"]["suggestedScore"]
    assert {sug3["home"], sug3["away"]} == {2, 1}
    assert max(sug3["home"], sug3["away"]) == 2
    if third["homeTeam"] == "Frankrijk":
        assert third["aiPrediction"]["pick"] == "1"
        assert sug3["home"] == 2 and sug3["away"] == 1
    else:
        assert third["aiPrediction"]["pick"] == "2"
        assert sug3["home"] == 1 and sug3["away"] == 2

    final = by_number[104]
    assert final["homeTeam"] == "Spanje"
    assert final["awayTeam"] == "Argentinië"
    assert final["aiPrediction"]["pick"] == "1"
    assert final["aiPrediction"]["suggestedScore"]["home"] == 3
    assert final["aiPrediction"]["suggestedScore"]["away"] == 2
    assert "Spanje" in str(final["aiPrediction"]["explanation"])
