"""Kansen en pick volgen uit dezelfde diff-gebaseerde logistic."""

from app.data.teams.context_score import match_context_breakdown
from app.predictions import _probabilities, predict_match
from app.teams import fifa_team_key


def test_diff_8_maps_to_about_58_percent_home_in_group() -> None:
    probs = _probabilities(8, can_draw=True)
    assert 54 <= probs["home"] <= 62
    assert probs["home"] + probs["draw"] + probs["away"] == 100


def test_usa_paraguay_pick_and_probs_aligned() -> None:
    pred = predict_match("USA", "Paraguay", "group", "1", "D")
    br = match_context_breakdown(fifa_team_key("USA"), fifa_team_key("Paraguay"))
    assert br["diff"] >= 6
    assert pred["pick"] == "1"
    assert pred["homeWinProbability"] == max(
        pred["homeWinProbability"],
        pred["drawProbability"],
        pred["awayWinProbability"],
    )
    assert pred["homeWinProbability"] >= 52


def test_large_favorite_has_strong_knockout_home_chance() -> None:
    pred = predict_match("Argentina", "Haiti", "knockout", "R16", None)
    assert pred["pick"] == "1"
    assert pred["homeWinProbability"] >= 78
    assert pred["drawProbability"] is None


def test_korea_czechia_even_match_pick_draw() -> None:
    pred = predict_match("Korea Republic", "Czechia", "group", "1", "A")
    assert pred["pick"] == "3"
    assert pred["drawProbability"] >= pred["homeWinProbability"]
    assert pred["drawProbability"] >= pred["awayWinProbability"]


def test_pick_always_matches_highest_probability() -> None:
    pairs = [
        ("USA", "Paraguay", "group"),
        ("Argentina", "Haiti", "knockout"),
        ("France", "Brazil", "group"),
        ("Qatar", "Switzerland", "group"),
    ]
    for home, away, stage in pairs:
        pred = predict_match(home, away, stage, "1", "A")
        probs = {
            "1": pred["homeWinProbability"],
            "3": pred["drawProbability"] or 0,
            "2": pred["awayWinProbability"],
        }
        assert pred["pick"] == max(probs, key=probs.get)
