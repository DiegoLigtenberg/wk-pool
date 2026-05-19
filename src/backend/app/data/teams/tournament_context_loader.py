"""Parse `tournament_context` uit team-YAML."""

from __future__ import annotations

from typing import Any

from app.data.teams.team_bundle import GroupFixture, GroupStage
from app.data.teams.tournament_context_schema import (
    HeadToHeadRecord,
    Momentum,
    PhaseFixturePlan,
    PlayedMatch,
    StandingsSnapshot,
    TournamentContext,
    TournamentPhase,
)
from app.teams import display_team_name, fifa_team_key, localize_teams_in_text

_VALID_PHASE_STATUS = frozenset({"upcoming", "in_progress", "completed", "eliminated", "not_applicable"})
_VALID_MOMENTUM = frozenset({"rising", "stable", "falling"})
_VALID_RESULT = frozenset({"W", "D", "L"})
_VALID_H2H_SCOPE = frozenset({"all_time", "world_cup", "recent"})


def _parse_momentum(raw: object | None) -> Momentum | None:
    if not isinstance(raw, dict):
        return None
    label = raw.get("label")
    if label is not None and label not in _VALID_MOMENTUM:
        raise ValueError(f"momentum.label must be one of {_VALID_MOMENTUM}")
    notes = raw.get("notes")
    return Momentum(
        label=label,  # type: ignore[arg-type]
        notes=localize_teams_in_text(str(notes)) if notes else None,
    )


def _parse_standings(raw: object | None) -> StandingsSnapshot | None:
    if not isinstance(raw, dict):
        return None
    return StandingsSnapshot(
        points=int(raw.get("points", 0)),
        played=int(raw.get("played", 0)),
        wins=int(raw.get("wins", 0)),
        draws=int(raw.get("draws", 0)),
        losses=int(raw.get("losses", 0)),
        goals_for=int(raw.get("goals_for", 0)),
        goals_against=int(raw.get("goals_against", 0)),
        position=int(raw["position"]) if raw.get("position") is not None else None,
    )


def _parse_played_matches(raw: object | None) -> tuple[PlayedMatch, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[PlayedMatch] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        opp_fifa = fifa_team_key(str(row.get("opponent_fifa") or row.get("opponent_nl", "")))
        result = row.get("result")
        if result is not None and result not in _VALID_RESULT:
            raise ValueError(f"played_matches.result must be W, D, L or null")
        out.append(
            PlayedMatch(
                match_number=int(row["match_number"]) if row.get("match_number") is not None else None,
                opponent_fifa=opp_fifa,
                opponent_nl=str(row.get("opponent_nl") or display_team_name(opp_fifa)),
                result=result,  # type: ignore[arg-type]
                score_for=int(row["score_for"]) if row.get("score_for") is not None else None,
                score_against=int(row["score_against"]) if row.get("score_against") is not None else None,
                stage_round=str(row["stage_round"]) if row.get("stage_round") else None,
                notes=localize_teams_in_text(str(row["notes"])) if row.get("notes") else None,
            )
        )
    return tuple(out)


def _parse_fixture_plan(raw: object | None) -> PhaseFixturePlan | None:
    if not isinstance(raw, dict) or not raw.get("fixtures"):
        return None
    fixtures: list[GroupFixture] = []
    for row in raw["fixtures"]:
        fixtures.append(
            GroupFixture(
                match_number=int(row["match_number"]),
                kickoff=str(row["kickoff"]),
                is_home=bool(row["is_home"]),
                opponent_fifa=str(row["opponent_fifa"]),
                opponent_nl=str(row["opponent_nl"]),
                stadium=str(row["stadium"]),
                narrative=row.get("narrative"),
            )
        )
    return PhaseFixturePlan(
        group=str(raw["group"]) if raw.get("group") else None,
        opponents_nl=tuple(raw.get("opponents_nl") or ()),
        opponents_fifa=tuple(raw.get("opponents_fifa") or ()),
        fixtures=tuple(fixtures),
        fixture_hooks=tuple(raw.get("fixture_hooks") or ()),
        schedule_rest_notes=raw.get("schedule_rest_notes"),
        venue_dispersion_notes=str(raw.get("venue_dispersion_notes") or ""),
        bracket_notes=str(raw["bracket_notes"]) if raw.get("bracket_notes") else None,
    )


def _parse_phase(phase_key: str, raw: object) -> TournamentPhase | None:
    if not isinstance(raw, dict):
        return None
    status = raw.get("status", "not_applicable" if phase_key == "knockout" else "upcoming")
    if status not in _VALID_PHASE_STATUS:
        raise ValueError(f"phases.{phase_key}.status invalid: {status!r}")
    return TournamentPhase(
        phase_key=phase_key,
        status=status,  # type: ignore[arg-type]
        fixture_plan=_parse_fixture_plan(raw.get("fixture_plan")),
        played_matches=_parse_played_matches(raw.get("played_matches")),
        standings=_parse_standings(raw.get("standings")),
        momentum=_parse_momentum(raw.get("momentum")),
        phase_notes=localize_teams_in_text(str(raw["phase_notes"])) if raw.get("phase_notes") else None,
    )


def _parse_head_to_head(raw: object | None) -> tuple[HeadToHeadRecord, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[HeadToHeadRecord] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        scope = row.get("scope", "all_time")
        if scope not in _VALID_H2H_SCOPE:
            raise ValueError(f"head_to_head.scope must be one of {_VALID_H2H_SCOPE}")
        opp_fifa = fifa_team_key(str(row.get("opponent_fifa") or row.get("opponent_nl", "")))
        out.append(
            HeadToHeadRecord(
                opponent_fifa=opp_fifa,
                opponent_nl=str(row.get("opponent_nl") or display_team_name(opp_fifa)),
                scope=scope,  # type: ignore[arg-type]
                wins=int(row.get("wins", 0)),
                draws=int(row.get("draws", 0)),
                losses=int(row.get("losses", 0)),
                notes=localize_teams_in_text(str(row["notes"])) if row.get("notes") else None,
                last_meeting=str(row["last_meeting"]) if row.get("last_meeting") else None,
            )
        )
    return tuple(out)


def parse_tournament_context(raw: object | None) -> TournamentContext | None:
    if not isinstance(raw, dict):
        return None
    phases_raw = raw.get("phases")
    if not isinstance(phases_raw, dict):
        return None
    phases: dict[str, TournamentPhase] = {}
    for key, value in phases_raw.items():
        phase = _parse_phase(str(key), value)
        if phase is not None:
            phases[str(key)] = phase
    return TournamentContext(
        schema_version=int(raw.get("schema_version", 1)),
        phases=phases,
        head_to_head=_parse_head_to_head(raw.get("head_to_head")),
    )


def group_stage_from_context(
    tc: TournamentContext | None, *, legacy_group_stage: object | None, fifa: str
) -> GroupStage:
    """fixture_plan uit tournament_context, anders legacy `group_stage` root."""
    if tc and "group" in tc.phases and tc.phases["group"].fixture_plan:
        plan = tc.phases["group"].fixture_plan
        return GroupStage(
            group=str(plan.group or ""),
            opponents_nl=plan.opponents_nl,
            opponents_fifa=plan.opponents_fifa,
            fixtures=plan.fixtures,  # type: ignore[arg-type]
            fixture_hooks=plan.fixture_hooks,
            schedule_rest_notes=plan.schedule_rest_notes,
            venue_dispersion_notes=plan.venue_dispersion_notes,
        )
    if isinstance(legacy_group_stage, dict) and legacy_group_stage.get("fixtures"):
        plan = _parse_fixture_plan(legacy_group_stage)
        assert plan is not None
        return GroupStage(
            group=str(plan.group or ""),
            opponents_nl=plan.opponents_nl,
            opponents_fifa=plan.opponents_fifa,
            fixtures=plan.fixtures,  # type: ignore[arg-type]
            fixture_hooks=plan.fixture_hooks,
            schedule_rest_notes=plan.schedule_rest_notes,
            venue_dispersion_notes=plan.venue_dispersion_notes,
        )
    from app.data.teams.fixture_schedule import group_stage_for_team

    return group_stage_for_team(fifa)


def head_to_head_vs(
    tc: TournamentContext | None, opponent_fifa: str, *, scope: str | None = None
) -> HeadToHeadRecord | None:
    if tc is None:
        return None
    opp = fifa_team_key(opponent_fifa)
    for row in tc.head_to_head:
        if row.opponent_fifa == opp and (scope is None or row.scope == scope):
            return row
    return None
