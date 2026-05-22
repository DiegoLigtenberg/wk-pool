"""Bouw `context_scoring` uit team-YAML ,  eenmalige ‘research → punten’-logica."""

from __future__ import annotations

from app.data.teams.context_scoring_schema import ContextFactor, ContextScoring
from app.data.teams.fixture_schedule import NOTABLE_FIXTURE_NARRATIVES
from app.data.teams.pairwise_matchup import _spark_is_opener_altitude, build_pairwise_factors
from app.data.teams.team_bundle import TeamBundle
from app.display_text import (
    clip_research_excerpt,
    humanize_factor_reason,
    humanize_matchup_shorthand,
    humanize_research_line,
    normalize_display_text,
)
from app.teams import display_team_name, fifa_team_key

MAX_PERSISTENT = 2
MAX_PER_OPPONENT = 2
MAX_PERSISTENT_DELTA = 3
MAX_OPPONENT_DELTA = 2


def _mentions_opponent(line: str, opponent_nl: str, opponent_fifa: str) -> bool:
    low = line.lower()
    return opponent_nl.lower() in low or opponent_fifa.lower() in low


def _collapse_style_matchups(factors: list[ContextFactor]) -> list[ContextFactor]:
    """Eén tactiek-regel per duel: netto delta, geen dubbele +1 op hetzelfde thema."""
    styles = [f for f in factors if f.id == "style_matchup"]
    if len(styles) <= 1:
        return factors
    rest = [f for f in factors if f.id != "style_matchup"]
    net = sum(f.delta for f in styles)
    if net == 0:
        return rest
    net = max(-1, min(1, net))
    primary = max(styles, key=lambda f: abs(f.delta))
    return rest + [ContextFactor(id="style_matchup", delta=net, reason=primary.reason)]


def _clip_factors(
    factors: list[ContextFactor],
    max_items: int,
    max_delta: int,
    *,
    priority_ids: frozenset[str] = frozenset(),
    balance_signs: bool = False,
) -> tuple[ContextFactor, ...]:
    picked: list[ContextFactor] = []
    total = 0
    priority = [f for f in factors if f.id in priority_ids]
    remaining = [f for f in factors if f.id not in priority_ids]

    for factor in priority:
        if len(picked) >= max_items:
            break
        picked.append(factor)
        total += factor.delta

    pool = sorted(remaining, key=lambda f: (abs(f.delta), f.delta), reverse=True)
    if balance_signs and len(picked) < max_items:
        for subset in (
            [f for f in pool if f.delta > 0],
            [f for f in pool if f.delta < 0],
        ):
            if not subset or len(picked) >= max_items:
                continue
            factor = subset[0]
            if factor in picked:
                continue
            if abs(total + factor.delta) > max_delta and total != 0:
                continue
            picked.append(factor)
            total += factor.delta

    for factor in pool:
        if len(picked) >= max_items:
            break
        if factor in picked:
            continue
        if factor.delta == 0 and factor.id not in ("fixture_story", "opener_context"):
            continue
        if abs(total + factor.delta) > max_delta and total != 0:
            continue
        picked.append(factor)
        total += factor.delta
    return tuple(picked)


def build_persistent_factors(bundle: TeamBundle) -> tuple[ContextFactor, ...]:
    """Max 2 vaste factoren ,  gelden in elke groepswedstrijd."""
    candidates: list[ContextFactor] = []

    if bundle.squad_load_notes:
        candidates.append(
            ContextFactor(
                id="squad_load",
                delta=-2,
                reason=humanize_research_line(
                    clip_research_excerpt(bundle.squad_load_notes), team_nl=bundle.team_name_nl
                ),
            )
        )

    if (
        bundle.distinctive_spark_notes
        and not bundle.squad_load_notes
        and not _spark_is_opener_altitude(bundle.distinctive_spark_notes)
    ):
        spark = bundle.distinctive_spark_notes
        delta = -2 if any(w in spark.lower() for w in ("out", "definitief", "afwezig", "kwiest")) else -1
        candidates.append(
            ContextFactor(
                id="distinctive_spark",
                delta=delta,
                reason=humanize_research_line(
                    clip_research_excerpt(spark), team_nl=bundle.team_name_nl
                ),
            )
        )

    if bundle.star_dependency == "high":
        candidates.append(
            ContextFactor(
                id="star_dependency",
                delta=-1,
                reason=normalize_display_text(
                    "Sterafhankelijkheid: weinig marge als de ster uit de wedstrijd is"
                ),
            )
        )
    if bundle.selection_drama_notes and len(candidates) < MAX_PERSISTENT:
        candidates.append(
            ContextFactor(
                id="selection_drama",
                delta=-1,
                reason=humanize_research_line(
                    clip_research_excerpt(bundle.selection_drama_notes),
                    team_nl=bundle.team_name_nl,
                ),
            )
        )

    if bundle.crowd_home_bias_notes and not bundle.cohost_status:
        candidates.append(
            ContextFactor(
                id="crowd_bias",
                delta=1,
                reason=humanize_research_line(
                    clip_research_excerpt(bundle.crowd_home_bias_notes),
                    team_nl=bundle.team_name_nl,
                ),
            )
        )

    if bundle.cohost_status and bundle.crowd_home_bias_notes:
        candidates.append(
            ContextFactor(
                id="cohost_crowd",
                delta=1,
                reason=humanize_research_line(
                    clip_research_excerpt(bundle.crowd_home_bias_notes, max_len=200),
                    team_nl=bundle.team_name_nl,
                ),
            )
        )

    return _clip_factors(candidates, MAX_PERSISTENT, MAX_PERSISTENT_DELTA)


def build_versus_factors(
    bundle: TeamBundle,
    opponent_fifa: str,
    opponent: TeamBundle | None = None,
) -> tuple[ContextFactor, ...]:
    """Max 2 factoren voor dit groepsduel (beide dossiers)."""
    opponent_fifa = fifa_team_key(opponent_fifa)
    opp_nl = display_team_name(opponent_fifa)
    candidates: list[ContextFactor] = []

    if opponent is not None:
        candidates.extend(build_pairwise_factors(bundle, opponent))

    for line in bundle.matchup_counters_us:
        if _mentions_opponent(line, opp_nl, opponent_fifa):
            candidates.append(
                ContextFactor(
                    id="matchup_risk",
                    delta=-1,
                    reason=humanize_matchup_shorthand(
                        clip_research_excerpt(line),
                        opp_nl,
                        team_nl=bundle.team_name_nl,
                        kind="risk",
                    ),
                )
            )

    for line in bundle.matchup_we_counter:
        if _mentions_opponent(line, opp_nl, opponent_fifa):
            candidates.append(
                ContextFactor(
                    id="matchup_edge",
                    delta=1,
                    reason=humanize_matchup_shorthand(
                        clip_research_excerpt(line),
                        opp_nl,
                        team_nl=bundle.team_name_nl,
                        kind="edge",
                    ),
                )
            )

    narrative = NOTABLE_FIXTURE_NARRATIVES.get((bundle.fifa_team_key, opponent_fifa))
    if narrative:
        delta = -1 if any(w in narrative.lower() for w in ("rematch", "titels", "underdog", "opener")) else 0
        candidates.append(
            ContextFactor(
                id="fixture_story", delta=delta, reason=clip_research_excerpt(narrative)
            )
        )

    for fx in bundle.group_stage.fixtures:
        if fx.opponent_fifa == opponent_fifa and fx.narrative and not narrative:
            candidates.append(
                ContextFactor(
                    id="fixture_story", delta=0, reason=clip_research_excerpt(fx.narrative)
                )
            )

    if bundle.discipline_risk_notes and _mentions_opponent(
        bundle.discipline_risk_notes, opp_nl, opponent_fifa
    ):
        candidates.append(
            ContextFactor(
                id="discipline",
                delta=-1,
                reason=humanize_research_line(
                    clip_research_excerpt(bundle.discipline_risk_notes),
                    team_nl=bundle.team_name_nl,
                ),
            )
        )

    return _clip_factors(
        _collapse_style_matchups(candidates),
        MAX_PER_OPPONENT,
        MAX_OPPONENT_DELTA,
        priority_ids=frozenset({"opener_context"}),
        balance_signs=True,
    )


def build_context_scoring(
    bundle: TeamBundle,
    all_bundles: dict[str, TeamBundle] | None = None,
) -> ContextScoring:
    persistent = build_persistent_factors(bundle)
    versus: dict[str, tuple[ContextFactor, ...]] = {}
    for opp_fifa in bundle.group_stage.opponents_fifa:
        opp = (all_bundles or {}).get(fifa_team_key(opp_fifa))
        versus[opp_fifa] = build_versus_factors(bundle, opp_fifa, opponent=opp)
    return _humanize_scoring_for_export(
        ContextScoring(persistent=persistent, versus=versus),
        bundle,
    )


def _humanize_scoring_for_export(
    scoring: ContextScoring,
    bundle: TeamBundle,
) -> ContextScoring:
    """Schrijf alleen leesbare zinnen naar YAML (geen 'In dit duel speelt mee')."""
    persistent = tuple(
        ContextFactor(
            id=f.id,
            delta=f.delta,
            reason=humanize_factor_reason(
                f.reason,
                factor_id=f.id,
                subject_team=bundle.team_name_nl,
                opponent_team="",
            ),
        )
        for f in scoring.persistent
    )
    versus: dict[str, tuple[ContextFactor, ...]] = {}
    for opp_fifa, factors in scoring.versus.items():
        opp_nl = display_team_name(opp_fifa)
        versus[opp_fifa] = tuple(
            ContextFactor(
                id=f.id,
                delta=f.delta,
                reason=humanize_factor_reason(
                    f.reason,
                    factor_id=f.id,
                    subject_team=bundle.team_name_nl,
                    opponent_team=opp_nl,
                ),
            )
            for f in factors
        )
    return ContextScoring(persistent=persistent, versus=versus)


def context_scoring_to_yaml_dict(scoring: ContextScoring) -> dict:
    return {
        "persistent": [
            {"id": f.id, "delta": f.delta, "reason": f.reason} for f in scoring.persistent
        ],
        "versus": {
            opp: [{"id": f.id, "delta": f.delta, "reason": f.reason} for f in factors]
            for opp, factors in scoring.versus.items()
        },
    }
