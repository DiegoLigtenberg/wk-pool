"""Group-stage form from synced match results (for knockout momentum)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.match_results_store import result_for_match

if TYPE_CHECKING:
    from app.tournament import Fixture


@dataclass(frozen=True)
class GroupFormStats:
    fifa_team: str
    group: str
    rank: int
    points: int
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    goal_log: tuple[int, ...] = ()

    @property
    def goals_per_game(self) -> float:
        if self.played == 0:
            return 0.0
        return self.goals_for / self.played

    @property
    def scoring_trend(self) -> int:
        """+1 stijgende scorelijn, −1 dalend, 0 neutraal (laatste vs eerdere duels)."""
        if len(self.goal_log) < 2:
            return 0
        earlier = self.goal_log[:-1]
        last = self.goal_log[-1]
        early_avg = sum(earlier) / len(earlier)
        if last >= early_avg + 1.0:
            return 1
        if last <= max(0.0, early_avg - 1.0):
            return -1
        return 0


def _apply_result(row: dict[str, int | list[int]], goals_for: int, goals_against: int) -> None:
    row["played"] = int(row["played"]) + 1
    row["goals_for"] = int(row["goals_for"]) + goals_for
    row["goals_against"] = int(row["goals_against"]) + goals_against
    if goals_for > goals_against:
        row["wins"] = int(row["wins"]) + 1
        row["points"] = int(row["points"]) + 3
    elif goals_for == goals_against:
        row["draws"] = int(row["draws"]) + 1
        row["points"] = int(row["points"]) + 1
    else:
        row["losses"] = int(row["losses"]) + 1


def build_group_form_index(
    fixtures: list[Fixture],
    results_store: dict[str, object],
) -> dict[str, GroupFormStats]:
    """FIFA team key → poule stats after completed group matches."""
    tables: dict[str, dict[str, dict[str, int | list[int]]]] = {}

    for fixture in fixtures:
        if fixture.group is None:
            continue
        group = fixture.group
        tables.setdefault(group, {})
        for team in (fixture.home_team, fixture.away_team):
            tables[group].setdefault(
                team,
                {
                    "points": 0,
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "goal_log": [],
                },
            )

        stored = result_for_match(results_store, fixture.match_number)
        if not stored or not isinstance(stored.get("score"), dict):
            continue

        home_goals = int(stored["score"]["home"])
        away_goals = int(stored["score"]["away"])
        home_row = tables[group][fixture.home_team]
        away_row = tables[group][fixture.away_team]
        _apply_result(home_row, home_goals, away_goals)
        _apply_result(away_row, away_goals, home_goals)
        home_row["goal_log"].append(home_goals)
        away_row["goal_log"].append(away_goals)

    index: dict[str, GroupFormStats] = {}
    for group, team_rows in tables.items():
        ranked = sorted(
            team_rows.items(),
            key=lambda item: (
                -item[1]["points"],
                -(item[1]["goals_for"] - item[1]["goals_against"]),
                -item[1]["goals_for"],
                item[0],
            ),
        )
        for rank, (fifa_team, row) in enumerate(ranked, start=1):
            gd = int(row["goals_for"]) - int(row["goals_against"])
            goal_log = tuple(int(g) for g in row["goal_log"])
            index[fifa_team] = GroupFormStats(
                fifa_team=fifa_team,
                group=group,
                rank=rank,
                points=int(row["points"]),
                played=int(row["played"]),
                wins=int(row["wins"]),
                draws=int(row["draws"]),
                losses=int(row["losses"]),
                goals_for=int(row["goals_for"]),
                goals_against=int(row["goals_against"]),
                goal_difference=gd,
                goal_log=goal_log,
            )
    return index


def group_stage_complete(fixtures: list[Fixture], results_store: dict[str, object]) -> bool:
    for fixture in fixtures:
        if fixture.group is None:
            continue
        if result_for_match(results_store, fixture.match_number) is None:
            return False
    return True


def live_form_tuple(
    home: GroupFormStats | None,
    away: GroupFormStats | None,
) -> tuple[int, int, int, int] | None:
    if home is None or away is None or home.played == 0 or away.played == 0:
        return None
    return home.points, home.played, away.points, away.played
