"""Runtime: som context_scoring + host → breakdown voor voorspelling."""

from __future__ import annotations

from dataclasses import dataclass

from app.data.teams.context_scoring_schema import ContextFactor, ContextScoring
from app.data.teams.factor_dedupe import (
    dedupe_cohost_host_factors,
    dedupe_overlapping_factors,
    dedupe_pair_factors,
)
from app.data.teams.factor_weights import (
    NARRATIVE_ZERO_IDS,
    FactorBucket,
    aggregate_weighted_side,
    context_adjustments_weighted,
    display_deltas_for_aggregate,
    factor_bucket,
    _allocate_proportional,
)
from app.data.teams.team_loader import get_team_bundle
from app.data.teams.team_registry import HOST_NATIONS
from app.display_text import humanize_factor_reason
from app.teams import display_team_name, fifa_team_key


@dataclass(frozen=True, slots=True)
class SideContextResult:
    factors: tuple[ContextFactor, ...]
    research_delta: int
    persistent_total: int
    duel_total: int
    host_delta: int
    travel_delta: int
    total_delta: int


def _raw_side_factors(team_fifa: str, opponent_fifa: str) -> list[ContextFactor]:
    bundle = get_team_bundle(team_fifa)
    scoring: ContextScoring | None = bundle.context_scoring
    factors: list[ContextFactor] = []

    if scoring is not None:
        factors.extend(scoring.persistent)
        factors.extend(scoring.versus.get(fifa_team_key(opponent_fifa), ()))

    if team_fifa in HOST_NATIONS:
        factors.append(
            ContextFactor(
                id="host_region",
                delta=1,
                reason="Co-host: thuisregio en publiek",
            )
        )
    return factors


def _context_from_factors(factors: list[ContextFactor]) -> SideContextResult:
    agg = aggregate_weighted_side(tuple(factors))
    display_by_id = display_deltas_for_aggregate(agg)
    display_factors = tuple(
        ContextFactor(
            id=wf.factor.id,
            delta=display_by_id.get(wf.factor.id, 0),
            reason=wf.factor.reason,
        )
        for wf in agg.factors
        if display_by_id.get(wf.factor.id, 0) != 0 or wf.factor.id in NARRATIVE_ZERO_IDS
    )
    return SideContextResult(
        factors=display_factors,
        research_delta=agg.research_total,
        persistent_total=agg.persistent_total,
        duel_total=agg.duel_total,
        host_delta=agg.host_total,
        travel_delta=agg.travel_total,
        total_delta=agg.total_delta,
    )


def _align_factor_deltas_to_totals(ctx: SideContextResult) -> SideContextResult:
    """Zorg dat zichtbare factor-deltas optellen tot contextDelta (na pair-scaling)."""
    factors = list(ctx.factors)
    host_items = [
        (f.id, f.delta) for f in factors if factor_bucket(f.id) == FactorBucket.HOST and f.delta != 0
    ]
    travel_items = [
        (f.id, f.delta)
        for f in factors
        if factor_bucket(f.id) == FactorBucket.TRAVEL and f.delta != 0
    ]
    persistent_items = [
        (f.id, f.delta)
        for f in factors
        if factor_bucket(f.id) == FactorBucket.PERSISTENT and f.delta != 0
    ]
    duel_items = [
        (f.id, f.delta)
        for f in factors
        if factor_bucket(f.id) == FactorBucket.DUEL and f.delta != 0
    ]
    display_by_id: dict[str, int] = {}
    from app.data.teams.factor_weights import _allocate_bucket_display

    display_by_id.update(_allocate_bucket_display(ctx.host_delta, host_items))
    display_by_id.update(_allocate_bucket_display(ctx.travel_delta, travel_items))
    display_by_id.update(_allocate_bucket_display(ctx.persistent_total, persistent_items))
    display_by_id.update(_allocate_bucket_display(ctx.duel_total, duel_items))

    aligned = tuple(
        ContextFactor(
            id=f.id,
            delta=display_by_id.get(f.id, 0),
            reason=f.reason,
        )
        for f in factors
        if display_by_id.get(f.id, 0) != 0 or f.id in NARRATIVE_ZERO_IDS
    )
    return SideContextResult(
        factors=aligned,
        research_delta=ctx.research_delta,
        persistent_total=ctx.persistent_total,
        duel_total=ctx.duel_total,
        host_delta=ctx.host_delta,
        travel_delta=ctx.travel_delta,
        total_delta=ctx.total_delta,
    )


def _pair_totals(
    home: SideContextResult,
    away: SideContextResult,
) -> tuple[SideContextResult, SideContextResult]:
    home_r, away_r = context_adjustments_weighted(home.research_delta, away.research_delta)
    if home_r == home.research_delta and away_r == away.research_delta:
        return home, away
    home_adj = SideContextResult(
        factors=home.factors,
        research_delta=home_r,
        persistent_total=home.persistent_total,
        duel_total=home.duel_total,
        host_delta=home.host_delta,
        travel_delta=home.travel_delta,
        total_delta=home_r + home.host_delta + home.travel_delta,
    )
    away_adj = SideContextResult(
        factors=away.factors,
        research_delta=away_r,
        persistent_total=away.persistent_total,
        duel_total=away.duel_total,
        host_delta=away.host_delta,
        travel_delta=away.travel_delta,
        total_delta=away_r + away.host_delta + away.travel_delta,
    )
    return _align_factor_deltas_to_totals(home_adj), _align_factor_deltas_to_totals(away_adj)


def _prepare_side_factors(team_fifa: str, opponent_fifa: str) -> list[ContextFactor]:
    factors = dedupe_overlapping_factors(_raw_side_factors(team_fifa, opponent_fifa))
    return dedupe_cohost_host_factors(factors)


def side_context(team_fifa: str, opponent_fifa: str) -> SideContextResult:
    return _context_from_factors(_prepare_side_factors(team_fifa, opponent_fifa))


def side_context_pair(home_fifa: str, away_fifa: str) -> tuple[SideContextResult, SideContextResult]:
    """Beide zijden met paar-dedupe (geen gespiegelde +/- op hetzelfde duelthema)."""
    home_fifa = fifa_team_key(home_fifa)
    away_fifa = fifa_team_key(away_fifa)
    home_factors = _prepare_side_factors(home_fifa, away_fifa)
    away_factors = _prepare_side_factors(away_fifa, home_fifa)
    home_factors, away_factors = dedupe_pair_factors(home_factors, away_factors)
    home = _context_from_factors(home_factors)
    away = _context_from_factors(away_factors)
    return _pair_totals(home, away)


def match_context_breakdown(home_fifa: str, away_fifa: str) -> dict[str, object]:
    home_fifa = fifa_team_key(home_fifa)
    away_fifa = fifa_team_key(away_fifa)
    home = get_team_bundle(home_fifa)
    away = get_team_bundle(away_fifa)

    home_ctx, away_ctx = side_context_pair(home_fifa, away_fifa)

    home_eff = home.power_score + home_ctx.total_delta
    away_eff = away.power_score + away_ctx.total_delta
    diff = home_eff - away_eff

    def _side_payload(
        team_fifa: str,
        ctx: SideContextResult,
        effective: int,
        opponent_fifa: str,
    ) -> dict[str, object]:
        bundle = get_team_bundle(team_fifa)
        opponent_nl = display_team_name(opponent_fifa)
        return {
            "team": bundle.team_name_nl,
            "powerScore": bundle.power_score,
            "researchDelta": ctx.research_delta,
            "hostDelta": ctx.host_delta,
            "travelDelta": ctx.travel_delta,
            "contextDelta": ctx.total_delta,
            "effectiveScore": effective,
            "reasons": [
                {
                    "id": f.id,
                    "delta": f.delta,
                    "reason": humanize_factor_reason(
                        f.reason,
                        factor_id=f.id,
                        subject_team=bundle.team_name_nl,
                        opponent_team=opponent_nl,
                    ),
                }
                for f in ctx.factors
                if f.delta != 0 or f.id in NARRATIVE_ZERO_IDS
            ],
        }

    return {
        "home": _side_payload(home_fifa, home_ctx, home_eff, away_fifa),
        "away": _side_payload(away_fifa, away_ctx, away_eff, home_fifa),
        "diff": diff,
        "summary": (
            f"{display_team_name(home_fifa)} effectief {home_eff} vs "
            f"{display_team_name(away_fifa)} {away_eff} (verschil {diff:+d})"
        ),
    }


def context_adjustments(home_fifa: str, away_fifa: str) -> tuple[int, int]:
    """Punten-equivalent thuis/uit voor diff (research max ±6 op het duel)."""
    home_fifa = fifa_team_key(home_fifa)
    away_fifa = fifa_team_key(away_fifa)
    home_ctx, away_ctx = side_context_pair(home_fifa, away_fifa)
    return home_ctx.total_delta, away_ctx.total_delta
