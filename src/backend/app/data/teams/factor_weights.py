"""Vaste herweging research-factoren → punten op wedstrijdscore (geen runtime-LLM).

Research-factoren: YAML ±1 → ±3 effectief. Upset/choke (matchup-specifiek) wegen zwaarder.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.data.teams.context_scoring_schema import ContextFactor

# --- Schalen ---

RESEARCH_POINT_SCALE = 3  # tactiek/matchup YAML ±1 → ±3 effectief
VOLATILITY_POINT_SCALE = 6  # upset_path / choke_risk YAML ±2 → ±12 effectief
HOST_BUCKET_MAX = 3
PERSISTENT_BUCKET_MAX = 9
DUEL_BUCKET_MAX = 12
VOLATILITY_BUCKET_MAX = 12
RESEARCH_SIDE_MAX = 24  # persistent + duel + volatility per kant (excl. host/away_fixture)
MATCHUP_DIFF_SOFT_CAP = 24  # |home_research| + |away_research| op het duel


class FactorBucket(str, Enum):
    HOST = "host"
    TRAVEL = "travel"
    PERSISTENT = "persistent"
    DUEL = "duel"
    NARRATIVE = "narrative"


HOST_FACTOR_IDS = frozenset({"host_region", "cohost_crowd", "home_fixture"})
TRAVEL_FACTOR_IDS = frozenset({"away_fixture"})
PERSISTENT_FACTOR_IDS = frozenset(
    {
        "squad_load",
        "distinctive_spark",
        "star_dependency",
        "selection_drama",
        "crowd_bias",
        "cohost_crowd",
    }
)
DUEL_FACTOR_IDS = frozenset(
    {
        "style_matchup",
        "tactical_weakness",
        "tactical_strength",
        "opponent_profile_weak",
        "opponent_profile_strong",
        "matchup_edge",
        "matchup_risk",
        "upset_path",
        "choke_risk",
        "psychology",
        "discipline",
        "home_fixture",
        "opener_context",
        "fixture_story",
        "fixture_narrative",
    }
)
NARRATIVE_ZERO_IDS = frozenset({"fixture_story", "opener_context", "fixture_narrative"})
VOLATILITY_FACTOR_IDS = frozenset({"upset_path", "choke_risk"})

_RESEARCH_SCALED_IDS = (
    PERSISTENT_FACTOR_IDS
    | DUEL_FACTOR_IDS
    | TRAVEL_FACTOR_IDS
) - HOST_FACTOR_IDS


def factor_bucket(factor_id: str) -> FactorBucket:
    if factor_id in HOST_FACTOR_IDS:
        return FactorBucket.HOST
    if factor_id in TRAVEL_FACTOR_IDS:
        return FactorBucket.TRAVEL
    if factor_id in PERSISTENT_FACTOR_IDS:
        return FactorBucket.PERSISTENT
    if factor_id in DUEL_FACTOR_IDS:
        return FactorBucket.DUEL
    return FactorBucket.NARRATIVE


def _point_scale(factor_id: str) -> int:
    if factor_id in HOST_FACTOR_IDS:
        return 1
    if factor_id in _RESEARCH_SCALED_IDS or factor_id in NARRATIVE_ZERO_IDS:
        return RESEARCH_POINT_SCALE
    return RESEARCH_POINT_SCALE


@dataclass(frozen=True, slots=True)
class WeightedFactor:
    factor: ContextFactor
    raw_delta: int
    effective_delta: int
    bucket: FactorBucket


@dataclass(frozen=True, slots=True)
class SideWeightedContext:
    factors: tuple[WeightedFactor, ...]
    host_total: int
    travel_total: int
    persistent_total: int
    duel_total: int
    volatility_total: int
    research_total: int
    total_delta: int


def effective_delta_for_factor(factor: ContextFactor) -> int:
    """Ruwe YAML/builder-delta → gewogen punten (research ×3; upset/choke ×6 op raw)."""
    raw = int(factor.delta)
    if raw == 0:
        return 0

    scale = _point_scale(factor.id)
    sign = 1 if raw > 0 else -1
    magnitude = min(abs(raw), 2)

    if factor.id == "host_region":
        return 2 if raw > 0 else 0

    if factor.id == "squad_load":
        return -RESEARCH_POINT_SCALE * magnitude if raw < 0 else 0

    if factor.id == "distinctive_spark":
        eff = -scale * magnitude
        return max(-2 * scale, min(-scale, eff))

    if factor.id == "upset_path":
        mag = min(abs(raw), 2)
        return mag * VOLATILITY_POINT_SCALE

    if factor.id == "choke_risk":
        mag = min(abs(raw), 2)
        return -mag * VOLATILITY_POINT_SCALE

    return sign * scale * magnitude


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def aggregate_weighted_side(
    factors: tuple[ContextFactor, ...],
    *,
    persistent_ids: frozenset[str] = PERSISTENT_FACTOR_IDS,
) -> SideWeightedContext:
    weighted: list[WeightedFactor] = []
    host_parts: list[int] = []
    travel_total = 0
    persistent_parts: list[int] = []
    duel_parts: list[int] = []
    volatility_parts: list[int] = []

    for factor in factors:
        eff = effective_delta_for_factor(factor)
        bucket = factor_bucket(factor.id)
        weighted.append(
            WeightedFactor(
                factor=factor,
                raw_delta=int(factor.delta),
                effective_delta=eff,
                bucket=bucket,
            )
        )

        if factor.id in HOST_FACTOR_IDS and eff > 0:
            host_parts.append(eff)
        elif factor.id in TRAVEL_FACTOR_IDS:
            travel_total += eff
        elif factor.id in VOLATILITY_FACTOR_IDS:
            if eff != 0:
                volatility_parts.append(eff)
        elif factor.id in persistent_ids and factor.id != "cohost_crowd":
            if eff != 0:
                persistent_parts.append(eff)
        elif factor.id == "cohost_crowd":
            if eff > 0:
                host_parts.append(eff)
        elif factor.id in DUEL_FACTOR_IDS and factor.id not in HOST_FACTOR_IDS:
            if eff != 0:
                duel_parts.append(eff)

    host_total = _clamp(sum(host_parts), 0, HOST_BUCKET_MAX)
    persistent_total = _clamp(sum(persistent_parts), -PERSISTENT_BUCKET_MAX, PERSISTENT_BUCKET_MAX)
    duel_total = _clamp(sum(duel_parts), -DUEL_BUCKET_MAX, DUEL_BUCKET_MAX)
    volatility_total = _clamp(
        sum(volatility_parts), -VOLATILITY_BUCKET_MAX, VOLATILITY_BUCKET_MAX
    )
    research_total = _clamp(
        persistent_total + duel_total + volatility_total,
        -RESEARCH_SIDE_MAX,
        RESEARCH_SIDE_MAX,
    )
    total_delta = research_total + host_total + travel_total

    return SideWeightedContext(
        factors=tuple(weighted),
        host_total=host_total,
        travel_total=travel_total,
        persistent_total=persistent_total,
        duel_total=duel_total,
        volatility_total=volatility_total,
        research_total=research_total,
        total_delta=total_delta,
    )


def _allocate_proportional(total: int, items: list[tuple[str, int]]) -> dict[str, int]:
    """Verdeel `total` over keys naar rato van gewicht (teken behouden); som = total."""
    if not items:
        return {}
    keys = [k for k, _ in items]
    if total == 0:
        return dict.fromkeys(keys, 0)

    weighted = [(k, w) for k, w in items if w != 0]
    if not weighted:
        return dict.fromkeys(keys, 0)

    wsum = sum(abs(w) for _, w in weighted)
    targets = [(k, total * w / wsum) for k, w in weighted]
    floors = {k: int(t) for k, t in targets}
    remainder = total - sum(floors.values())
    if remainder != 0:
        ranked = sorted(
            targets,
            key=lambda row: abs(row[1] - int(row[1])),
            reverse=True,
        )
        step = 1 if remainder > 0 else -1
        for i in range(abs(remainder)):
            k = ranked[i % len(ranked)][0]
            floors[k] = floors.get(k, 0) + step

    for k in keys:
        floors.setdefault(k, 0)
    return floors


def _allocate_bucket_display(total: int, items: list[tuple[str, int]]) -> dict[str, int]:
    """Toon per-factor deltas; vermijd teken-flip bij gemengde tekens in de bucket."""
    if not items:
        return {}
    item_sum = sum(w for _, w in items)
    if item_sum == total:
        return {k: w for k, w in items}
    if total == 0 and any(w != 0 for _, w in items):
        return {k: w for k, w in items}
    return _allocate_proportional(total, items)


def display_deltas_for_aggregate(agg: SideWeightedContext) -> dict[str, int]:
    """Per-factor deltas voor UI; som = total_delta (na bucket-caps)."""
    host_items = [
        (wf.factor.id, wf.effective_delta)
        for wf in agg.factors
        if wf.bucket == FactorBucket.HOST and wf.effective_delta != 0
    ]
    travel_items = [
        (wf.factor.id, wf.effective_delta)
        for wf in agg.factors
        if wf.bucket == FactorBucket.TRAVEL and wf.effective_delta != 0
    ]
    persistent_items = [
        (wf.factor.id, wf.effective_delta)
        for wf in agg.factors
        if wf.bucket == FactorBucket.PERSISTENT and wf.effective_delta != 0
    ]
    duel_items = [
        (wf.factor.id, wf.effective_delta)
        for wf in agg.factors
        if wf.bucket == FactorBucket.DUEL
        and wf.factor.id not in VOLATILITY_FACTOR_IDS
        and wf.effective_delta != 0
    ]
    volatility_items = [
        (wf.factor.id, wf.effective_delta)
        for wf in agg.factors
        if wf.factor.id in VOLATILITY_FACTOR_IDS and wf.effective_delta != 0
    ]

    out: dict[str, int] = {}
    out.update(_allocate_bucket_display(agg.host_total, host_items))
    out.update(_allocate_bucket_display(agg.travel_total, travel_items))
    out.update(_allocate_bucket_display(agg.persistent_total, persistent_items))
    out.update(_allocate_bucket_display(agg.duel_total, duel_items))
    out.update(_allocate_bucket_display(agg.volatility_total, volatility_items))
    for wf in agg.factors:
        out.setdefault(wf.factor.id, 0)
    return out


def scale_matchup_research(
    home_research: int,
    away_research: int,
) -> tuple[int, int]:
    """Beperk totale matchup-impact op diff."""
    total = abs(home_research) + abs(away_research)
    if total <= MATCHUP_DIFF_SOFT_CAP:
        return home_research, away_research
    scale = MATCHUP_DIFF_SOFT_CAP / total
    return round(home_research * scale), round(away_research * scale)


def context_adjustments_weighted(
    home_research: int,
    away_research: int,
) -> tuple[int, int]:
    return scale_matchup_research(home_research, away_research)
