"""Runtime: som context_scoring + host → breakdown voor voorspelling."""

from __future__ import annotations

from dataclasses import dataclass

from app.data.teams.context_scoring_schema import ContextFactor, ContextScoring
from app.data.teams.factor_dedupe import dedupe_overlapping_factors
from app.data.teams.team_loader import get_team_bundle
from app.data.teams.team_registry import HOST_NATIONS
from app.display_text import humanize_factor_reason
from app.teams import display_team_name, fifa_team_key

SIDE_CONTEXT_CAP = 5


@dataclass(frozen=True, slots=True)
class SideContextResult:
    factors: tuple[ContextFactor, ...]
    research_delta: int
    host_delta: int
    total_delta: int


def _sum_factors(factors: tuple[ContextFactor, ...]) -> int:
    return max(-SIDE_CONTEXT_CAP, min(SIDE_CONTEXT_CAP, sum(f.delta for f in factors)))


def side_context(team_fifa: str, opponent_fifa: str) -> SideContextResult:
    bundle = get_team_bundle(team_fifa)
    scoring: ContextScoring | None = bundle.context_scoring
    factors: list[ContextFactor] = []

    if scoring is not None:
        factors.extend(scoring.persistent)
        factors.extend(scoring.versus.get(fifa_team_key(opponent_fifa), ()))

    host_delta = 3 if team_fifa in HOST_NATIONS else 0
    if host_delta:
        factors.append(
            ContextFactor(
                id="host_region",
                delta=host_delta,
                reason="Co-host: thuisregio en publiek",
            )
        )

    factors = dedupe_overlapping_factors(factors)

    research_delta = _sum_factors(tuple(f for f in factors if f.id != "host_region"))
    total = research_delta + host_delta

    return SideContextResult(
        factors=tuple(factors),
        research_delta=research_delta,
        host_delta=host_delta,
        total_delta=total,
    )


def match_context_breakdown(home_fifa: str, away_fifa: str) -> dict[str, object]:
    home_fifa = fifa_team_key(home_fifa)
    away_fifa = fifa_team_key(away_fifa)
    home = get_team_bundle(home_fifa)
    away = get_team_bundle(away_fifa)

    home_ctx = side_context(home_fifa, away_fifa)
    away_ctx = side_context(away_fifa, home_fifa)

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
                if f.delta != 0 or f.id in ("fixture_story", "opener_context")
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
    """Punten-equivalent thuis/uit voor diff (max totaal ±6 op het duel)."""
    home_fifa = fifa_team_key(home_fifa)
    away_fifa = fifa_team_key(away_fifa)
    home_ctx = side_context(home_fifa, away_fifa)
    away_ctx = side_context(away_fifa, home_fifa)

    home_adj = home_ctx.total_delta
    away_adj = away_ctx.total_delta
    total = abs(home_adj) + abs(away_adj)
    if total > 6:
        scale = 6 / total
        home_adj = round(home_adj * scale)
        away_adj = round(away_adj * scale)

    return home_adj, away_adj
