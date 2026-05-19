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
    if any(w in low for w in ("opener", "2240", "azteca")) and any(
        w in low for w in ("hoogte", "acclimatisatie", "2240", "fysieke test")
    ):
        return "opener_altitude"
    return None


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
