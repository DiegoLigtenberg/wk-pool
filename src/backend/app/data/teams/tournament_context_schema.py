"""Generiek tornooi-context schema (groep + knock-out + onderlinge historie)."""

from __future__ import annotations

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.data.teams.team_bundle import GroupFixture

PhaseStatus = Literal["upcoming", "in_progress", "completed", "eliminated", "not_applicable"]
MomentumLabel = Literal["rising", "stable", "falling"]
MatchResult = Literal["W", "D", "L"]
HeadToHeadScope = Literal["all_time", "world_cup", "recent"]


@dataclass(frozen=True, slots=True)
class Momentum:
    label: MomentumLabel | None
    notes: str | None


@dataclass(frozen=True, slots=True)
class StandingsSnapshot:
    points: int
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    position: int | None


@dataclass(frozen=True, slots=True)
class PlayedMatch:
    """Gespeelde wedstrijd in een fase (groep of knock-out)."""

    match_number: int | None
    opponent_fifa: str
    opponent_nl: str
    result: MatchResult | None
    score_for: int | None
    score_against: int | None
    stage_round: str | None  # bv. group / round_of_16 / quarter_final
    notes: str | None


@dataclass(frozen=True, slots=True)
class HeadToHeadRecord:
    opponent_fifa: str
    opponent_nl: str
    scope: HeadToHeadScope
    wins: int
    draws: int
    losses: int
    notes: str | None
    last_meeting: str | None = None


@dataclass(frozen=True, slots=True)
class PhaseFixturePlan:
    """Geplande wedstrijden (uit CSV sync of later bracket)."""

    group: str | None
    opponents_nl: tuple[str, ...]
    opponents_fifa: tuple[str, ...]
    fixtures: tuple["GroupFixture", ...]
    fixture_hooks: tuple[str, ...]
    schedule_rest_notes: str | None
    venue_dispersion_notes: str
    bracket_notes: str | None = None  # knock-out: pad naar finale


@dataclass(frozen=True, slots=True)
class TournamentPhase:
    phase_key: str  # group | knockout | round_of_16 | ...
    status: PhaseStatus
    fixture_plan: PhaseFixturePlan | None
    played_matches: tuple[PlayedMatch, ...]
    standings: StandingsSnapshot | None
    momentum: Momentum | None
    phase_notes: str | None


@dataclass(frozen=True, slots=True)
class TournamentContext:
    schema_version: int
    phases: dict[str, TournamentPhase]
    head_to_head: tuple[HeadToHeadRecord, ...]
