"""Vul `teams/{slug}.yaml` aan met ratings + groepsfase uit CSV.

Behoudt handmatige velden in `tournament_context` (gespeelde wedstrijden, momentum, H2H).

Run na handmatige research-edits:
    cd src/backend
    python -m app.data.teams.sync_research_yaml
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.data.teams.fixture_schedule import group_stage_for_team
from app.data.teams.team_registry import CONFEDERATIONS, HOST_NATIONS, TEAM_SLUGS
from app.predictions import TEAM_PROFILES
from app.teams import display_team_name

RESEARCH_DIR = Path(__file__).resolve().parent / "research"

# Velden die sync NIET overschrijft (handmatig tijdens tornooi).
_PHASE_MANUAL_KEYS = ("status", "played_matches", "standings", "momentum", "phase_notes")


def _fixture_plan_dict(fifa: str) -> dict[str, Any]:
    stage = group_stage_for_team(fifa)
    return {
        "group": stage.group,
        "opponents_nl": list(stage.opponents_nl),
        "opponents_fifa": list(stage.opponents_fifa),
        "fixtures": [
            {
                "match_number": fx.match_number,
                "kickoff": fx.kickoff,
                "is_home": fx.is_home,
                "opponent_fifa": fx.opponent_fifa,
                "opponent_nl": fx.opponent_nl,
                "stadium": fx.stadium,
                **({"narrative": fx.narrative} if fx.narrative else {}),
            }
            for fx in stage.fixtures
        ],
        "fixture_hooks": list(stage.fixture_hooks),
        "schedule_rest_notes": stage.schedule_rest_notes,
        "venue_dispersion_notes": stage.venue_dispersion_notes,
    }


def _default_group_phase(fixture_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "upcoming",
        "fixture_plan": fixture_plan,
        "played_matches": [],
        "standings": {
            "points": 0,
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "position": None,
        },
        "momentum": {"label": None, "notes": None},
        "phase_notes": None,
    }


def _default_knockout_phase() -> dict[str, Any]:
    return {
        "status": "not_applicable",
        "fixture_plan": None,
        "played_matches": [],
        "momentum": {"label": None, "notes": None},
        "phase_notes": None,
    }


def _merge_phase(existing: object | None, fresh_fixture_plan: dict[str, Any]) -> dict[str, Any]:
    merged = _default_group_phase(fresh_fixture_plan)
    if isinstance(existing, dict):
        for key in _PHASE_MANUAL_KEYS:
            if key in existing:
                merged[key] = existing[key]
    merged["fixture_plan"] = fresh_fixture_plan
    return merged


def _merge_knockout(existing: object | None) -> dict[str, Any]:
    merged = _default_knockout_phase()
    if isinstance(existing, dict):
        for key in (*_PHASE_MANUAL_KEYS, "fixture_plan"):
            if key in existing:
                merged[key] = existing[key]
    return merged


def _build_tournament_context(data: dict[str, Any], fifa: str, fixture_plan: dict[str, Any]) -> dict[str, Any]:
    existing = data.get("tournament_context")
    phases_existing: dict[str, Any] = {}
    head_to_head: list[Any] = []
    schema_version = 1

    if isinstance(existing, dict):
        schema_version = int(existing.get("schema_version", 1))
        if isinstance(existing.get("phases"), dict):
            phases_existing = existing["phases"]
        if isinstance(existing.get("head_to_head"), list):
            head_to_head = existing["head_to_head"]

    return {
        "schema_version": schema_version,
        "phases": {
            "group": _merge_phase(phases_existing.get("group"), fixture_plan),
            "knockout": _merge_knockout(phases_existing.get("knockout")),
        },
        "head_to_head": head_to_head,
    }


def main() -> None:
    for fifa, slug in sorted(TEAM_SLUGS.items()):
        path = RESEARCH_DIR / f"{slug}.yaml"
        data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
        profile = TEAM_PROFILES[fifa]
        fixture_plan = _fixture_plan_dict(fifa)

        data["team_id"] = display_team_name(fifa)
        data["slug"] = slug
        data["power_score"] = profile.rating
        data["tier"] = profile.tier
        data["macro_style"] = profile.style
        data["strengths"] = list(profile.strengths)
        data["risks"] = list(profile.risks)
        data["confederation"] = CONFEDERATIONS[fifa]
        data["cohost_status"] = fifa in HOST_NATIONS
        data["tournament_context"] = _build_tournament_context(data, fifa, fixture_plan)
        # Legacy root key ,  zelfde als fixture_plan; loader accepteert beide.
        data["group_stage"] = fixture_plan

        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
    print(f"Synced {len(TEAM_SLUGS)} files in {RESEARCH_DIR}")


if __name__ == "__main__":
    main()
