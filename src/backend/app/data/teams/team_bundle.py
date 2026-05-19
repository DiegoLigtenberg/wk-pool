"""Volledig teamdossier per land (YAML + CSV-verrijking)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.data.teams.context_scoring_schema import ContextScoring
    from app.data.teams.tournament_context_schema import TournamentContext


@dataclass(frozen=True, slots=True)
class GroupFixture:
    match_number: int
    kickoff: str
    is_home: bool
    opponent_fifa: str
    opponent_nl: str
    stadium: str
    narrative: str | None = None


@dataclass(frozen=True, slots=True)
class GroupStage:
    group: str
    opponents_nl: tuple[str, ...]
    opponents_fifa: tuple[str, ...]
    fixtures: tuple[GroupFixture, ...]
    fixture_hooks: tuple[str, ...]
    schedule_rest_notes: str | None
    venue_dispersion_notes: str


@dataclass(frozen=True, slots=True)
class TeamBundle:
    """Eén land ,  bron voor voorspelling, UI en matchup-logica."""

    fifa_team_key: str
    team_name_nl: str
    slug: str
    context_as_of: str
    sources: tuple[str, ...]
    analyzed: tuple[str, ...]
    power_score: int
    tier: str
    macro_style: str
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    confederation: str
    cohost_status: bool
    interpretive_ceiling_vs_floor: str
    phase_preferences: tuple[str, str]
    transition_orientation_summary: str
    psychology_intro: str
    psychology_vectors: tuple[str, str]
    matchup_counters_us: tuple[str, ...]
    matchup_we_counter: tuple[str, ...]
    dead_ball_swings_matches: str
    experience_cohesion_notes: tuple[str, ...]
    group_stage: GroupStage
    tournament_context: "TournamentContext | None" = None
    context_scoring: "ContextScoring | None" = None
    heat_altitude_acclimatization_notes: str | None = None
    intercontinental_travel_profile: str | None = None
    distinctive_spark_notes: str | None = None
    crowd_home_bias_notes: str | None = None
    selection_drama_notes: str | None = None
    star_dependency: str | None = None
    club_concentration_notes: str | None = None
    squad_load_notes: str | None = None
    discipline_risk_notes: str | None = None

    @property
    def yaml_path(self) -> str:
        return f"teams/{self.slug}.yaml"
