"""Laad volledige teamdossiers uit `teams/{slug}.yaml` (+ CSV waar nodig)."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.data.teams.context_scoring_builder import build_context_scoring
from app.data.teams.context_scoring_loader import parse_context_scoring
from app.data.teams.team_bundle import GroupStage, TeamBundle
from app.data.teams.tournament_context_loader import group_stage_from_context, parse_tournament_context
from app.data.teams.team_registry import CONFEDERATIONS, HOST_NATIONS, TEAM_SLUGS
from app.teams import display_team_name, fifa_team_key, localize_teams_in_text

TEAMS_DIR = Path(__file__).resolve().parent


def _as_tuple_str(value: object, *, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list) and all(isinstance(x, str) for x in value):
        return tuple(value)
    raise TypeError(f"{label} must be str or list[str]")


def _as_pair(value: object, *, label: str) -> tuple[str, str]:
    if not isinstance(value, list) or len(value) != 2 or not all(isinstance(x, str) for x in value):
        raise TypeError(f"{label} must be a list of exactly 2 strings")
    return value[0], value[1]


def _normalize_experience_notes(raw: object) -> tuple[str, ...]:
    notes = _as_tuple_str(raw, label="experience_cohesion_notes")
    if len(notes) > 5 and all(len(part) == 1 for part in notes):
        return ("".join(notes),)
    return notes


def _parse_bundle(path: Path, data: dict[str, Any]) -> TeamBundle:
    fifa = fifa_team_key(str(data["team_id"]))
    slug = str(data.get("slug") or path.stem)
    if TEAM_SLUGS.get(fifa) != slug:
        raise ValueError(f"{path}: slug {slug!r} hoort bij {TEAM_SLUGS.get(fifa)!r}, niet {fifa!r}")

    star = data.get("star_dependency")
    if star is not None and star not in ("high", "medium"):
        raise ValueError(f"{path}: star_dependency must be high, medium, or omitted")

    if "power_score" not in data:
        raise ValueError(f"{path}: power_score ontbreekt ,  run sync_research_yaml")

    tournament_context = parse_tournament_context(data.get("tournament_context"))
    group_stage = group_stage_from_context(
        tournament_context,
        legacy_group_stage=data.get("group_stage"),
        fifa=fifa,
    )
    psych_a, psych_b = _as_pair(data["psychology_vectors"], label="psychology_vectors")

    def nl(value: str | None) -> str | None:
        return localize_teams_in_text(value) if value else None

    context_scoring = parse_context_scoring(data.get("context_scoring"))
    bundle = TeamBundle(
        fifa_team_key=fifa,
        team_name_nl=display_team_name(fifa),
        slug=slug,
        context_as_of=str(data.get("context_as_of", "2026-05-19")),
        sources=tuple(data.get("sources") or ()),
        analyzed=tuple(data.get("analyzed") or ()),
        power_score=int(data["power_score"]),
        tier=str(data["tier"]),
        macro_style=str(data["macro_style"]),
        strengths=_as_tuple_str(data["strengths"], label="strengths"),
        risks=_as_tuple_str(data["risks"], label="risks"),
        confederation=str(data.get("confederation") or CONFEDERATIONS[fifa]),
        cohost_status=bool(data.get("cohost_status", fifa in HOST_NATIONS)),
        interpretive_ceiling_vs_floor=nl(data["interpretive_ceiling_vs_floor"]) or "",
        phase_preferences=_as_pair(data["phase_preferences"], label="phase_preferences"),
        transition_orientation_summary=nl(data["transition_orientation_summary"]) or "",
        psychology_intro=nl(data["psychology_intro"]) or "",
        psychology_vectors=(nl(psych_a) or "", nl(psych_b) or ""),
        matchup_counters_us=_as_tuple_str(data["matchup_counters_us"], label="matchup_counters_us"),
        matchup_we_counter=_as_tuple_str(data["matchup_we_counter"], label="matchup_we_counter"),
        dead_ball_swings_matches=nl(data["dead_ball_swings_matches"]) or "",
        experience_cohesion_notes=_normalize_experience_notes(data["experience_cohesion_notes"]),
        group_stage=group_stage,
        tournament_context=tournament_context,
        heat_altitude_acclimatization_notes=nl(data.get("heat_altitude_acclimatization_notes")),
        intercontinental_travel_profile=nl(data.get("intercontinental_travel_profile")),
        distinctive_spark_notes=nl(data.get("distinctive_spark_notes")),
        crowd_home_bias_notes=nl(data.get("crowd_home_bias_notes")),
        selection_drama_notes=nl(data.get("selection_drama_notes")),
        star_dependency=star,
        club_concentration_notes=nl(data.get("club_concentration_notes")),
        squad_load_notes=nl(data.get("squad_load_notes")),
        discipline_risk_notes=nl(data.get("discipline_risk_notes")),
        context_scoring=context_scoring,
    )
    return bundle


@lru_cache(maxsize=1)
def load_all_bundles() -> dict[str, TeamBundle]:
    by_fifa: dict[str, TeamBundle] = {}
    for path in sorted((TEAMS_DIR / "research").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        bundle = _parse_bundle(path, data)
        if bundle.fifa_team_key in by_fifa:
            raise ValueError(f"Duplicate FIFA key {bundle.fifa_team_key!r}")
        by_fifa[bundle.fifa_team_key] = bundle
    for fifa, bundle in list(by_fifa.items()):
        if bundle.context_scoring is None:
            by_fifa[fifa] = replace(bundle, context_scoring=build_context_scoring(bundle, by_fifa))
    return by_fifa


def get_team_bundle(team: str) -> TeamBundle:
    return load_all_bundles()[fifa_team_key(team)]
