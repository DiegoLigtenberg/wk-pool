"""Voorkom dubbele factoren (zelfde onderwerp in groep + duel)."""

from __future__ import annotations

from app.data.teams.context_scoring_schema import ContextFactor

MATCH_SCOPED_IDS = frozenset(
    {
        "style_matchup",
        "opponent_profile_weak",
        "opponent_profile_strong",
        "tactical_weakness",
        "tactical_strength",
        "matchup_risk",
        "matchup_edge",
        "fixture_story",
        "psychology",
        "home_fixture",
        "away_fixture",
        "opener_context",
        "fixture_narrative",
        "discipline",
    }
)

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


def factor_topic_key(reason: str) -> str | None:
    low = reason.lower()
    if "xavi simons" in low or ("simons" in low and "knie" in low):
        return "simons_out"
    if "isidor" in low:
        return "isidor_core"
    if any(w in low for w in ("opener", "2240", "azteca")) and any(
        w in low for w in ("hoogte", "acclimatisatie", "2240", "fysieke test")
    ):
        return "opener_altitude"
    if "clarke" in low and "compact" in low:
        return "clarke_compact"
    return None


def _style_is_counter_vs_compact(reason: str) -> bool:
    low = reason.lower()
    return any(w in low for w in ("omschakeling", "counter", "transit")) and any(
        w in low for w in ("compact", "blok", "laag")
    )


def _style_is_opponent_counter_threat(reason: str) -> bool:
    low = reason.lower()
    return any(w in low for w in ("counter", "omschakel", "transit")) and any(
        w in low for w in ("aanval", "opbouw", "gevaarlijk")
    )


def _dedupe_within_side(factors: list[ContextFactor]) -> list[ContextFactor]:
    """Zelfde duel: compact-blok in +1 tactiek maakt aparte Clarke/compact-risico overbodig."""
    has_counter_compact_plus = any(
        f.id == "style_matchup" and f.delta > 0 and _style_is_counter_vs_compact(f.reason)
        for f in factors
    )
    if not has_counter_compact_plus:
        return factors
    out: list[ContextFactor] = []
    for factor in factors:
        if factor.id == "matchup_risk" and factor_topic_key(factor.reason) == "clarke_compact":
            continue
        if factor.id == "matchup_risk" and "compact" in factor.reason.lower():
            continue
        out.append(factor)
    return out


def dedupe_pair_factors(
    home_factors: list[ContextFactor],
    away_factors: list[ContextFactor],
) -> tuple[list[ContextFactor], list[ContextFactor]]:
    """Spiegelende duel-factoren tussen beide ploegen (zelfde thema, + en -)."""
    home = _dedupe_within_side(dedupe_overlapping_factors(list(home_factors)))
    away = _dedupe_within_side(dedupe_overlapping_factors(list(away_factors)))

    home_topics = {
        factor_topic_key(f.reason)
        for f in home
        if factor_topic_key(f.reason) and f.id in PERSISTENT_FACTOR_IDS
    }
    if "isidor_core" in home_topics:
        away = [
            f
            for f in away
            if not (f.id == "matchup_edge" and "isidor" in f.reason.lower())
        ]

    away_topics = {
        factor_topic_key(f.reason)
        for f in away
        if factor_topic_key(f.reason) and f.id in PERSISTENT_FACTOR_IDS
    }
    if "isidor_core" in away_topics:
        home = [
            f
            for f in home
            if not (f.id == "matchup_edge" and "isidor" in f.reason.lower())
        ]

    home_plus = next(
        (f for f in home if f.id == "style_matchup" and f.delta > 0 and _style_is_counter_vs_compact(f.reason)),
        None,
    )
    away_minus = next(
        (
            f
            for f in away
            if f.id == "style_matchup" and f.delta < 0 and _style_is_opponent_counter_threat(f.reason)
        ),
        None,
    )
    if home_plus and away_minus:
        away = [f for f in away if f is not away_minus]

    away_plus = next(
        (f for f in away if f.id == "style_matchup" and f.delta > 0 and _style_is_counter_vs_compact(f.reason)),
        None,
    )
    home_minus = next(
        (
            f
            for f in home
            if f.id == "style_matchup" and f.delta < 0 and _style_is_opponent_counter_threat(f.reason)
        ),
        None,
    )
    if away_plus and home_minus:
        home = [f for f in home if f is not home_minus]

    def _is_compact_block_theme(reason: str) -> bool:
        low = reason.lower()
        if "compact" not in low:
            return False
        return any(
            token in low
            for token in (
                "blok",
                "block",
                "opbouw",
                "frustreren",
                "moeilijk maken",
                "laag",
            )
        )

    home_opp_strong = next(
        (f for f in home if f.id == "opponent_profile_strong" and f.delta < 0),
        None,
    )
    away_tac_strong = next(
        (f for f in away if f.id == "tactical_strength" and f.delta > 0),
        None,
    )
    if (
        home_opp_strong
        and away_tac_strong
        and _is_compact_block_theme(home_opp_strong.reason)
        and _is_compact_block_theme(away_tac_strong.reason)
    ):
        home = [f for f in home if f is not home_opp_strong]

    away_opp_strong = next(
        (f for f in away if f.id == "opponent_profile_strong" and f.delta < 0),
        None,
    )
    home_tac_strong = next(
        (f for f in home if f.id == "tactical_strength" and f.delta > 0),
        None,
    )
    if (
        away_opp_strong
        and home_tac_strong
        and _is_compact_block_theme(away_opp_strong.reason)
        and _is_compact_block_theme(home_tac_strong.reason)
    ):
        away = [f for f in away if f is not away_opp_strong]

    if any(f.id == "matchup_edge" and "opener" in f.reason.lower() for f in home):
        away = [
            f
            for f in away
            if not (f.id == "psychology" and "opener" in f.reason.lower())
        ]
    if any(f.id == "matchup_edge" and "opener" in f.reason.lower() for f in away):
        home = [
            f
            for f in home
            if not (f.id == "matchup_edge" and "opener" in f.reason.lower())
        ]

    return home, away


def dedupe_overlapping_factors(factors: list[ContextFactor]) -> list[ContextFactor]:
    """Laat duel-factoren weg als hetzelfde onderwerp al in de hele groepsfase staat."""
    team_topics: set[str] = set()
    for factor in factors:
        if factor.id in PERSISTENT_FACTOR_IDS:
            key = factor_topic_key(factor.reason)
            if key:
                team_topics.add(key)

    if not team_topics:
        return factors

    out: list[ContextFactor] = []
    for factor in factors:
        if factor.id in MATCH_SCOPED_IDS:
            key = factor_topic_key(factor.reason)
            if key and key in team_topics:
                continue
        out.append(factor)
    return out
