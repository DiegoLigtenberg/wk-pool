from app.group_form import GroupFormStats
from app.pool_edge import group_scoring_trend_adjustments
from app.predictions import predict_match
from app.score_prediction import suggest_match_score


def test_suggest_match_score_for_tight_knockout_draw() -> None:
    score = suggest_match_score(
        pick="3",
        adjusted_diff=1,
        stage="knockout",
        home_goals_per_game=1.3,
        away_goals_per_game=1.0,
    )
    assert score["home"] == score["away"]
    assert score["home"] in (0, 1, 2)


def test_scoring_trend_adjustment_from_goal_log() -> None:
    home = GroupFormStats(
        fifa_team="Mexico",
        group="A",
        rank=1,
        points=7,
        played=3,
        wins=2,
        draws=1,
        losses=0,
        goals_for=6,
        goals_against=2,
        goal_difference=4,
        goal_log=(1, 1, 4),
    )
    away = GroupFormStats(
        fifa_team="Ecuador",
        group="E",
        rank=2,
        points=4,
        played=3,
        wins=1,
        draws=1,
        losses=1,
        goals_for=3,
        goals_against=4,
        goal_difference=-1,
        goal_log=(1, 1, 1),
    )
    adj = group_scoring_trend_adjustments(home, away)
    kinds = {a.id for a in adj}
    assert "home_scoring_trend" in kinds


def test_group_match_has_no_suggested_score() -> None:
    pred = predict_match("Mexico", "South Africa", "group", "1", "A")
    assert "suggestedScore" not in pred


def test_knockout_includes_suggested_score() -> None:
    pred = predict_match("Argentina", "France", "knockout", "Final", None)
    assert "suggestedScore" in pred
    assert pred["suggestedScore"]["home"] >= 0
    assert pred["suggestedScore"]["away"] >= 0


def test_tight_knockout_can_pick_draw_after_90() -> None:
    home = GroupFormStats(
        fifa_team="Netherlands",
        group="F",
        rank=1,
        points=5,
        played=3,
        wins=1,
        draws=2,
        losses=0,
        goals_for=4,
        goals_against=3,
        goal_difference=1,
        goal_log=(1, 2, 1),
    )
    away = GroupFormStats(
        fifa_team="Morocco",
        group="C",
        rank=1,
        points=5,
        played=3,
        wins=1,
        draws=2,
        losses=0,
        goals_for=4,
        goals_against=3,
        goal_difference=1,
        goal_log=(1, 2, 1),
    )
    pred = predict_match(
        "Netherlands",
        "Morocco",
        "knockout",
        "Round of 32",
        None,
        group_forms=(home, away),
    )
    assert pred["drawProbability"] is not None
    assert pred["pick"] == "3"
    assert pred["suggestedScore"]["home"] == pred["suggestedScore"]["away"]


def test_netherlands_morocco_knockout_override() -> None:
    pred = predict_match(
        "Netherlands",
        "Morocco",
        "knockout",
        "Round of 32",
        None,
        match_number=75,
    )
    assert pred["pick"] == "1"
    assert pred["suggestedScore"] == {
        "home": 3,
        "away": 2,
        "reason": "Pool-inschatting: Nederland wint na 90 minuten (3-2).",
    }


def test_knockout_winner_score_capped_at_two_goal_margin() -> None:
    heavy_fav = suggest_match_score(
        pick="1",
        adjusted_diff=20,
        stage="knockout",
        home_goals_per_game=2.5,
        away_goals_per_game=0.5,
    )
    assert heavy_fav["home"] <= 2
    assert heavy_fav["away"] <= 1
    assert heavy_fav["home"] - heavy_fav["away"] <= 2

    away_fav = suggest_match_score(
        pick="2",
        adjusted_diff=18,
        stage="knockout",
        home_goals_per_game=0.5,
        away_goals_per_game=2.5,
    )
    assert away_fav["away"] <= 2
    assert away_fav["home"] - away_fav["away"] >= -2


def test_knockout_draw_prefers_one_one_over_two_two() -> None:
    score = suggest_match_score(
        pick="3",
        adjusted_diff=1,
        stage="knockout",
        home_goals_per_game=2.0,
        away_goals_per_game=2.0,
    )
    assert score == {"home": 1, "away": 1, "reason": score["reason"]}


def test_knockout_away_winner_allows_home_goal_when_attackive() -> None:
    score = suggest_match_score(
        pick="2",
        adjusted_diff=10,
        stage="knockout",
        home_goals_per_game=1.0,
        away_goals_per_game=2.0,
    )
    assert score == {"home": 1, "away": 2, "reason": score["reason"]}


def test_knockout_draw_band_stricter_than_group() -> None:
    from app.predictions import (
        KNOCKOUT_DRAW_ABS_DIFF_MAX,
        GROUP_DRAW_ABS_DIFF_MAX,
        _pick_from_diff,
    )

    assert KNOCKOUT_DRAW_ABS_DIFF_MAX < GROUP_DRAW_ABS_DIFF_MAX
    assert _pick_from_diff(5, can_draw=True, home_power=72, away_power=71) == "3"
    assert (
        _pick_from_diff(
            5,
            can_draw=True,
            home_power=72,
            away_power=71,
            draw_abs_diff_max=KNOCKOUT_DRAW_ABS_DIFF_MAX,
        )
        == "1"
    )
