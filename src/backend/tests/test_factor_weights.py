"""Herweging research-factoren en co-host buckets."""

from app.data.teams.context_score import match_context_breakdown
from app.data.teams.factor_weights import (
    HOST_BUCKET_MAX,
    effective_delta_for_factor,
    aggregate_weighted_side,
)
from app.data.teams.context_scoring_schema import ContextFactor
from app.predictions import predict_match
from app.teams import fifa_team_key


def test_host_region_effective_two_not_three() -> None:
    eff = effective_delta_for_factor(
        ContextFactor(id="host_region", delta=1, reason="Co-host")
    )
    assert eff == 2


def test_display_factor_deltas_sum_to_context_delta() -> None:
    br = match_context_breakdown(fifa_team_key("USA"), fifa_team_key("Paraguay"))
    for side_key in ("home", "away"):
        side = br[side_key]
        factor_sum = sum(int(r["delta"]) for r in side["reasons"] if int(r["delta"]) != 0)
        assert factor_sum == side["contextDelta"], (
            f"{side_key}: factors sum {factor_sum} != contextDelta {side['contextDelta']}"
        )


def test_cohost_host_bucket_capped() -> None:
    factors = (
        ContextFactor(id="host_region", delta=1, reason="Co-host"),
        ContextFactor(id="cohost_crowd", delta=1, reason="Publiek"),
        ContextFactor(id="home_fixture", delta=1, reason="Thuis"),
    )
    agg = aggregate_weighted_side(factors)
    assert agg.host_total == HOST_BUCKET_MAX


def test_usa_paraguay_cohost_not_over_stacked() -> None:
    br = match_context_breakdown(fifa_team_key("USA"), fifa_team_key("Paraguay"))
    usa = br["home"]
    paraguay = br["away"]
    assert usa["hostDelta"] <= HOST_BUCKET_MAX
    assert usa["hostDelta"] >= 1
    assert usa["effectiveScore"] == 78 + usa["contextDelta"]
    assert paraguay["effectiveScore"] == 72 + paraguay["contextDelta"]
    assert usa["contextDelta"] <= 6


def test_qatar_switzerland_matchup_edge_about_qatar_not_swiss_coach() -> None:
    br = match_context_breakdown(fifa_team_key("Qatar"), fifa_team_key("Switzerland"))
    swiss_reasons = " ".join(r["reason"] for r in br["away"]["reasons"]).lower()
    assert "lopetegui zet bij zwitserland" not in swiss_reasons
    assert "qatar" in swiss_reasons or "lopetegui" in swiss_reasons
    pred = predict_match("Qatar", "Switzerland", "group", "1", "B")
    assert pred["pick"] == "2"


def test_squad_load_scaled_under_option_b() -> None:
    eff = effective_delta_for_factor(
        ContextFactor(id="squad_load", delta=-2, reason="Blessures")
    )
    assert eff == -6
