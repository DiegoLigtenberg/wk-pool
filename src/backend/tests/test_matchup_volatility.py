"""Matchup-specifieke upset/choke-factoren."""

from app.data.teams.context_score import match_context_breakdown
from app.data.teams.context_scoring_schema import ContextFactor
from app.data.teams.factor_weights import effective_delta_for_factor
from app.data.teams.matchup_volatility_loader import parse_matchup_volatility
from app.pool_edge import collect_pick_adjustments
from app.teams import fifa_team_key


def test_parse_matchup_volatility_upset_and_choke() -> None:
    parsed = parse_matchup_volatility(
        {
            "Portugal": {"upset": "Fysiek verrassingspad."},
            "Congo DR": {"choke": "Slordige opener."},
        }
    )
    assert parsed[fifa_team_key("Portugal")]["upset"] == "Fysiek verrassingspad."
    assert parsed[fifa_team_key("Congo DR")]["choke"] == "Slordige opener."


def test_upset_path_and_choke_effective_delta_heavy() -> None:
    assert (
        effective_delta_for_factor(
            ContextFactor(id="upset_path", delta=2, reason="x")
        )
        == 12
    )
    assert (
        effective_delta_for_factor(
            ContextFactor(id="choke_risk", delta=-2, reason="x")
        )
        == -12
    )


def test_congo_portugal_has_matchup_upset_and_choke() -> None:
    br = match_context_breakdown(fifa_team_key("Portugal"), fifa_team_key("Congo DR"))
    away_ids = {r["id"] for r in br["away"]["reasons"]}
    home_ids = {r["id"] for r in br["home"]["reasons"]}
    assert "upset_path" in away_ids
    assert "choke_risk" in home_ids
    upset = next(r for r in br["away"]["reasons"] if r["id"] == "upset_path")
    assert int(upset["delta"]) == 12


def test_portugal_congo_triggers_tactical_upset_adjustment() -> None:
    br = match_context_breakdown(fifa_team_key("Portugal"), fifa_team_key("Congo DR"))
    adj = collect_pick_adjustments(
        home_key=fifa_team_key("Portugal"),
        away_key=fifa_team_key("Congo DR"),
        home_power=int(br["home"]["powerScore"]),
        away_power=int(br["away"]["powerScore"]),
        home_factors=list(br["home"]["reasons"]),
        away_factors=list(br["away"]["reasons"]),
    )
    kinds = {a.kind for a in adj}
    assert "upset" in kinds
    upset = next(a for a in adj if a.kind == "upset")
    assert upset.delta < 0


def test_belgium_nz_crowd_bias_sign_matches_yaml() -> None:
    br = match_context_breakdown(fifa_team_key("Belgium"), fifa_team_key("New Zealand"))
    crowd = next((r for r in br["away"]["reasons"] if r["id"] == "crowd_bias"), None)
    assert crowd is not None
    assert int(crowd["delta"]) > 0


def test_egypt_belgium_has_upset_path() -> None:
    br = match_context_breakdown(fifa_team_key("Belgium"), fifa_team_key("Egypt"))
    away_ids = {r["id"] for r in br["away"]["reasons"]}
    assert "upset_path" in away_ids
