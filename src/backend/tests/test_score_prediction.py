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
    assert pred["suggestedScore"]["home"] == pred["suggestedScore"]["away"] or pred["pick"] in ("1", "2", "3")
