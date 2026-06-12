from app.crystal_ball import build_crystal_ball_view
from app.crystal_ball_research import load_crystal_ball_research
from app.tournament import build_tournament_view


def test_crystal_ball_has_twelve_group_winners() -> None:
    tournament = build_tournament_view()
    crystal = tournament["crystalBall"]

    assert len(crystal["groupWinners"]) == 12
    assert len(crystal["projectedGroups"]) == 12
    assert len(crystal["bonusQuestions"]) == 4


def test_crystal_ball_bonus_loaded_from_research() -> None:
    research = load_crystal_ball_research()
    tournament = build_tournament_view()
    crystal = tournament["crystalBall"]

    assert crystal["contextAsOf"] == research["contextAsOf"]
    assert crystal["bonusQuestions"][0]["id"] == "yellow_cards_total"
    assert crystal["bonusQuestions"][0]["value"] == "368"
    assert crystal["bonusQuestions"][2]["value"] == "Frankrijk"


def test_projected_standings_apply_all_group_picks() -> None:
    tournament = build_tournament_view()
    group_a = next(group for group in tournament["groups"] if group["name"] == "A")
    crystal_a = next(group for group in tournament["crystalBall"]["projectedGroups"] if group["name"] == "A")

    # Poule-view has no played matches until real results are ingested.
    assert max(int(row["played"]) for row in group_a["standings"]) == 0
    # Crystal Ball simulates all six group matches from AI picks.
    assert all(int(row["played"]) == 3 for row in crystal_a["standings"])
    assert crystal_a["winner"] == crystal_a["standings"][0]["team"]


def test_group_winner_prediction_pending_without_results() -> None:
    tournament = build_tournament_view()
    group = next(group for group in tournament["groups"] if group["name"] == "A")
    crystal_winner = next(entry for entry in tournament["crystalBall"]["groupWinners"] if entry["group"] == "A")

    assert group["predictedWinner"]
    assert group["winnerPredictionStatus"] == "pending"
    assert crystal_winner["team"] == group["predictedWinner"]
    assert crystal_winner["status"] == "pending"


def test_crystal_ball_includes_live_api_stats() -> None:
    tournament = build_tournament_view()
    live = tournament["crystalBall"]["liveStats"]

    assert live["source"] == "espn"
    assert live["totalMatches"] == 104
    assert live["completedMatches"] == tournament["summary"]["completed"]
    assert live["yellowCards"] == tournament["cardTotals"]["yellowCards"]
    assert live["directRedCards"] == tournament["cardTotals"]["directRedCards"]
    assert live["topScorer"] is None
