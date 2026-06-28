"""Pool-edge: pick uit kansen, upsets, live vorm."""

from app.data.teams.context_score import match_context_breakdown
from app.pool_edge import apply_adjustments, collect_pick_adjustments
from app.predictions import _pick_from_diff, _probabilities, predict_match
from app.teams import fifa_team_key
from app.tournament import load_fixtures


def test_group_draw_rate_near_quarter() -> None:
    draws = 0
    for fx in load_fixtures():
        if not fx.group:
            continue
        pred = predict_match(
            fx.home_team, fx.away_team, "group", "1", fx.group, match_number=fx.match_number
        )
        if pred["pick"] == "3":
            draws += 1
    assert 14 <= draws <= 22, f"expected ~25% draws, got {draws}/72"


def test_canada_bosnia_pick_matches_favorite_rule() -> None:
    pred = predict_match("Canada", "Bosnia and Herzegovina", "group", "1", "I")
    assert pred["pick"] in ("1", "3")
    detail = str(pred["insight"].get("scoreSummary", ""))
    assert detail.strip()
    assert str(pred["insight"].get("pickLogicNote", "")).strip() == ""
    low = detail.lower()
    if pred["pick"] == "1":
        assert "gelijkspel" not in pred["insight"]["verdict"].lower()
        assert any(
            w in low for w in ("sterk", "papier", "gelijk", "kansen", "sterkere", "favoriet")
        )
    else:
        assert "gelijk" in low


def test_upset_can_shift_diff_when_signals_strong() -> None:
    br = match_context_breakdown(fifa_team_key("Brazil"), fifa_team_key("Morocco"))
    adj = collect_pick_adjustments(
        home_key=fifa_team_key("Brazil"),
        away_key=fifa_team_key("Morocco"),
        home_power=int(br["home"]["powerScore"]),
        away_power=int(br["away"]["powerScore"]),
        home_factors=list(br["home"]["reasons"]),
        away_factors=list(br["away"]["reasons"]),
    )
    base = int(br["diff"])
    adjusted = apply_adjustments(base, adj)
    assert isinstance(adjusted, int)


def test_group_pre_wk_has_no_live_form_from_demo_csv() -> None:
    """Groepsfase = één statische poule vóór het WK; geen vorm uit fake gespeelde wedstrijden."""
    for fx in load_fixtures():
        if not fx.group:
            continue
        pred = predict_match(
            fx.home_team,
            fx.away_team,
            "group",
            "1",
            fx.group,
            match_number=fx.match_number,
        )
        kinds = {a.get("kind") for a in pred["insight"].get("poolAdjustments", [])}
        assert "live_form" not in kinds


def test_knockout_without_yaml_played_has_no_live_form() -> None:
    pred = predict_match("Argentina", "France", "knockout", "Final", None)
    kinds = {a.get("kind") for a in pred["insight"].get("poolAdjustments", [])}
    assert "live_form" not in kinds


def test_group_momentum_adjustments_on_knockout() -> None:
    from app.group_form import GroupFormStats

    home = GroupFormStats(
        fifa_team="Germany",
        group="E",
        rank=1,
        points=7,
        played=3,
        wins=2,
        draws=1,
        losses=0,
        goals_for=8,
        goals_against=2,
        goal_difference=6,
    )
    away = GroupFormStats(
        fifa_team="Paraguay",
        group="D",
        rank=3,
        points=4,
        played=3,
        wins=1,
        draws=1,
        losses=1,
        goals_for=3,
        goals_against=5,
        goal_difference=-2,
    )
    pred = predict_match(
        "Germany",
        "Paraguay",
        "knockout",
        "Round of 32",
        None,
        group_forms=(home, away),
    )
    labels = [a.get("label") for a in pred["insight"].get("poolAdjustments", [])]
    assert any("Poule" in str(label) for label in labels)
