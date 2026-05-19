"""YAML teamdossiers en context-scoring."""

from app.data.teams.context_score import context_adjustments
from app.data.teams.team_loader import get_team_bundle, load_all_bundles
from app.predictions import predict_match
from app.teams import display_team_name


def test_all_teams_load_from_yaml() -> None:
    bundles = load_all_bundles()
    assert len(bundles) == 48
    nl = get_team_bundle("Netherlands")
    assert nl.team_name_nl == "Nederland"
    assert nl.power_score == 85
    assert len(nl.group_stage.fixtures) == 3
    assert "Japan" in nl.group_stage.opponents_nl


def test_context_adjustment_bounded() -> None:
    home_adj, away_adj = context_adjustments("Netherlands", "Japan")
    assert abs(home_adj) <= 5
    assert abs(away_adj) <= 5
    assert abs(home_adj) + abs(away_adj) <= 6


def test_predict_includes_match_insight() -> None:
    pred = predict_match("Netherlands", "Japan", "group", "1", "F")
    insight = pred["insight"]
    assert insight is not None
    assert insight["home"]["powerScore"] == 85
    assert any(f["delta"] != 0 for f in insight["home"]["factors"])


def test_predict_uses_yaml_power_score() -> None:
    pred = predict_match("Netherlands", "Japan", "group", "1", "F")
    assert pred["pick"] in ("1", "2", "3")
    text = pred["explanation"] + " " + pred["insight"]["narrative"]
    assert display_team_name("Japan") in text or "Japan" in text
