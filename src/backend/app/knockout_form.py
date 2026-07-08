"""Knockout-round form (R32, R16, …) from synced results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.match_results_store import result_for_match
from app.data.teams.team_loader import get_team_bundle

if TYPE_CHECKING:
    from app.tournament import Fixture

_KO_ROUND_ORDER: dict[str, int] = {
    "Round of 32": 32,
    "Round of 16": 16,
    "Quarter Finals": 8,
    "Semi Finals": 4,
    "Finals": 2,
}


def _round_rank(name: str) -> int:
    return _KO_ROUND_ORDER.get(name, 0)


@dataclass(frozen=True)
class KnockoutRoundStats:
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    upset_wins: int
    max_upset_power_gap: int

    @property
    def goals_per_game(self) -> float:
        if self.played == 0:
            return 0.0
        return self.goals_for / self.played


def _team_power(fifa_team: str) -> int:
    return get_team_bundle(fifa_team).power_score


def _apply_ko_result(
    row: dict[str, int],
    *,
    goals_for: int,
    goals_against: int,
    opponent_power: int,
    own_power: int,
) -> None:
    row["played"] += 1
    row["goals_for"] += goals_for
    row["goals_against"] += goals_against
    if goals_for > goals_against:
        row["wins"] += 1
        gap = opponent_power - own_power
        if gap >= 6:
            row["upset_wins"] += 1
            row["max_upset_gap"] = max(row["max_upset_gap"], gap)
    elif goals_for == goals_against:
        row["draws"] += 1
    else:
        row["losses"] += 1


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
        if _round_rank(fixture.round_number) <= _round_rank(before_round):
            continue
        home, away = resolved_teams.get(fixture.match_number, (None, None))
        if not home or not away:
            continue
        stored = result_for_match(results_store, fixture.match_number)
        if not stored or not isinstance(stored.get("score"), dict):
            continue
        hg = int(stored["score"]["home"])
        ag = int(stored["score"]["away"])
        home_power = _team_power(home)
        away_power = _team_power(away)
        for team, gf, ga, opp_power, own_power in (
            (home, hg, ag, away_power, home_power),
            (away, ag, hg, home_power, away_power),
        ):
            row = rows.setdefault(
                team,
                {
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "upset_wins": 0,
                    "max_upset_gap": 0,
                },
            )
            _apply_ko_result(
                row,
                goals_for=gf,
                goals_against=ga,
                opponent_power=opp_power,
                own_power=own_power,
            )

    return {
        team: KnockoutRoundStats(
            played=row["played"],
            wins=row["wins"],
            draws=row["draws"],
            losses=row["losses"],
            goals_for=row["goals_for"],
            goals_against=row["goals_against"],
            upset_wins=row["upset_wins"],
            max_upset_power_gap=row["max_upset_gap"],
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
