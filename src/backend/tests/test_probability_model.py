"""Pick volgt wedstrijdscore (diff); kansen zijn daarop afgestemd."""

from app.data.teams.context_score import match_context_breakdown
from app.predictions import _pick_from_diff, _probabilities, predict_match
from app.teams import fifa_team_key


def test_probabilities_sum_to_100() -> None:
    probs = _probabilities(6, can_draw=True)
    assert probs["home"] + probs["draw"] + probs["away"] == 100


def test_usa_paraguay_pick_and_probs_aligned() -> None:
    pred = predict_match("USA", "Paraguay", "group", "1", "D")
    br = match_context_breakdown(fifa_team_key("USA"), fifa_team_key("Paraguay"))
    assert br["diff"] <= 6
    assert pred["pick"] in ("1", "3")
    probs = {
        "1": pred["homeWinProbability"],
        "3": pred["drawProbability"],
        "2": pred["awayWinProbability"],
    }
    assert probs[pred["pick"]] == max(probs.values())


def test_large_favorite_has_strong_knockout_home_chance() -> None:
    pred = predict_match("Argentina", "Haiti", "knockout", "R16", None)
    assert pred["pick"] == "1"
    assert pred["homeWinProbability"] >= 78
    assert pred["drawProbability"] is not None
    assert pred["suggestedScore"]["home"] > pred["suggestedScore"]["away"]


def test_korea_czechia_close_match_may_pick_draw() -> None:
    pred = predict_match("Korea Republic", "Czechia", "group", "1", "A")
    assert pred["pick"] in ("1", "2", "3")
    assert pred["drawProbability"] >= pred["homeWinProbability"]
    assert pred["drawProbability"] >= pred["awayWinProbability"]


def test_close_diff_picks_draw_not_exact_zero_only() -> None:
    pred = predict_match("Bosnia and Herzegovina", "Qatar", "group", "1", "I")
    br = match_context_breakdown(
        fifa_team_key("Bosnia and Herzegovina"), fifa_team_key("Qatar")
    )
    assert abs(br["diff"]) <= 2
    assert pred["drawProbability"] is not None and pred["drawProbability"] >= 25
    assert pred["pick"] in ("1", "2", "3")
    assert _pick_from_diff(int(br["diff"]), can_draw=True) in ("1", "2", "3")


def test_clear_diff_picks_winner() -> None:
    pred = predict_match("Argentina", "Haiti", "group", "1", "F")
    br = match_context_breakdown(fifa_team_key("Argentina"), fifa_team_key("Haiti"))
    assert br["diff"] >= 15
    assert pred["pick"] == "1"


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
