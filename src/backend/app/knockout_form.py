"""Knockout-round form (R32, R16, …) from synced results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.match_results_store import result_for_match

if TYPE_CHECKING:
    from app.tournament import Fixture

_KO_ROUND_ORDER: dict[str, int] = {
    "Round of 32": 32,
    "Round of 16": 16,
    "Quarter-final": 8,
    "Semi-final": 4,
    "Third place": 2,
    "Final": 1,
}


def _round_rank(name: str) -> int:
    return _KO_ROUND_ORDER.get(name, 0)


@dataclass(frozen=True)
class KnockoutRoundStats:
    played: int
    goals_for: int
    goals_against: int

    @property
    def goals_per_game(self) -> float:
        if self.played == 0:
            return 0.0
        return self.goals_for / self.played


def build_knockout_round_form_index(
    fixtures: list[Fixture],
    results_store: dict[str, object],
    resolved_teams: dict[int, tuple[str | None, str | None]],
    *,
    before_round: str,
) -> dict[str, KnockoutRoundStats]:
    """Goals per team in completed KO rounds strictly before `before_round`."""
    rows: dict[str, dict[str, int]] = {}

    for fixture in fixtures:
        if fixture.group is not None:
            continue
        if _round_rank(fixture.round_number) >= _round_rank(before_round):
            continue
        home, away = resolved_teams.get(fixture.match_number, (None, None))
        if not home or not away:
            continue
        stored = result_for_match(results_store, fixture.match_number)
        if not stored or not isinstance(stored.get("score"), dict):
            continue
        hg = int(stored["score"]["home"])
        ag = int(stored["score"]["away"])
        for team, gf, ga in ((home, hg, ag), (away, ag, hg)):
            row = rows.setdefault(team, {"played": 0, "goals_for": 0, "goals_against": 0})
            row["played"] += 1
            row["goals_for"] += gf
            row["goals_against"] += ga

    return {
        team: KnockoutRoundStats(
            played=row["played"],
            goals_for=row["goals_for"],
            goals_against=row["goals_against"],
        )
        for team, row in rows.items()
    }


def blended_goals_per_game(
    group_gpg: float,
    knockout_gpg: float,
    *,
    knockout_played: int,
) -> float:
    """Mix poule + vorige KO-ronde voor uitslag-suggestie (R16+)."""
    if knockout_played <= 0:
        return group_gpg
    if group_gpg <= 0:
        return knockout_gpg
    return 0.55 * group_gpg + 0.45 * knockout_gpg
