"""Resolve knockout CSV placeholders from group standings + FIFA Annex C."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from app.group_form import GroupFormStats, build_group_form_index, group_stage_complete

if TYPE_CHECKING:
    from app.tournament import Fixture

ANNEX_PATH = Path(__file__).resolve().parent / "data" / "fifa_annex_c_third_place.json"

# R32 fixtures where the home side is group winner X and away is a third-placed team.
THIRD_PLACE_HOME_WINNER: dict[int, str] = {
    74: "E",
    77: "I",
    79: "A",
    80: "L",
    82: "G",
    81: "D",
    85: "B",
    87: "K",
}


@dataclass(frozen=True)
class KnockoutBracketState:
    group_rankings: dict[str, list[str]]
    qualifying_third_groups: frozenset[str]
    annex_map: dict[str, str]
    resolved_teams: dict[int, tuple[str | None, str | None]]


@lru_cache(maxsize=1)
def _annex_data() -> tuple[tuple[str, ...], dict[str, dict[str, str]]]:
    payload = json.loads(ANNEX_PATH.read_text(encoding="utf-8"))
    winners = tuple(payload["winners"])
    lookup = {key: value for key, value in payload["lookup"].items()}
    return winners, lookup


def _parse_placed_slot(code: str) -> tuple[int, str] | None:
    if code in {"", "To be announced"}:
        return None
    if len(code) == 2 and code[0] in "12" and code[1].isalpha():
        return int(code[0]), code[1].upper()
    return None


def _group_rankings(form_index: dict[str, GroupFormStats]) -> dict[str, list[str]]:
    by_group: dict[str, list[tuple[int, str]]] = {}
    for stats in form_index.values():
        by_group.setdefault(stats.group, []).append((stats.rank, stats.fifa_team))
    return {
        group: [team for _, team in sorted(rows, key=lambda row: row[0])]
        for group, rows in by_group.items()
    }


def _rank_third_place_groups(form_index: dict[str, GroupFormStats]) -> list[str]:
    thirds: list[GroupFormStats] = [s for s in form_index.values() if s.rank == 3]
    thirds.sort(
        key=lambda row: (-row.points, -row.goal_difference, -row.goals_for, row.group),
    )
    return [row.group for row in thirds[:8]]


def _annex_map_for_groups(qualifying_groups: frozenset[str]) -> dict[str, str] | None:
    if len(qualifying_groups) != 8:
        return None
    _, lookup = _annex_data()
    key = "".join(sorted(qualifying_groups))
    return lookup.get(key)


def _team_at_group_rank(rankings: dict[str, list[str]], group: str, position: int) -> str | None:
    teams = rankings.get(group)
    if not teams or len(teams) < position:
        return None
    return teams[position - 1]


def _resolve_third_for_winner(
    *,
    winner_group: str,
    rankings: dict[str, list[str]],
    annex_map: dict[str, str],
) -> str | None:
    third_group = annex_map.get(winner_group)
    if not third_group:
        return None
    return _team_at_group_rank(rankings, third_group, 3)


def build_knockout_bracket_state(
    fixtures: list[Fixture],
    results_store: dict[str, object],
) -> KnockoutBracketState | None:
    if not group_stage_complete(fixtures, results_store):
        return None

    form_index = build_group_form_index(fixtures, results_store)
    rankings = _group_rankings(form_index)
    qualifying = frozenset(_rank_third_place_groups(form_index))
    annex_map = _annex_map_for_groups(qualifying)
    if annex_map is None:
        return None

    resolved: dict[int, tuple[str | None, str | None]] = {}
    for fixture in fixtures:
        if fixture.group is not None:
            continue
        home = _resolve_slot(
            fixture.home_team,
            fixture=fixture,
            side="home",
            rankings=rankings,
            annex_map=annex_map,
        )
        away = _resolve_slot(
            fixture.away_team,
            fixture=fixture,
            side="away",
            rankings=rankings,
            annex_map=annex_map,
        )
        resolved[fixture.match_number] = (home, away)

    return KnockoutBracketState(
        group_rankings=rankings,
        qualifying_third_groups=qualifying,
        annex_map=annex_map,
        resolved_teams=resolved,
    )


def _resolve_slot(
    code: str,
    *,
    fixture: Fixture,
    side: str,
    rankings: dict[str, list[str]],
    annex_map: dict[str, str],
) -> str | None:
    placed = _parse_placed_slot(code)
    if placed is not None:
        position, group = placed
        return _team_at_group_rank(rankings, group, position)

    if code.startswith("3") and side == "away":
        winner_group = THIRD_PLACE_HOME_WINNER.get(fixture.match_number)
        if winner_group:
            return _resolve_third_for_winner(
                winner_group=winner_group,
                rankings=rankings,
                annex_map=annex_map,
            )

    return None


def resolve_knockout_teams(
    fixture: Fixture,
    bracket: KnockoutBracketState | None,
) -> tuple[str, str]:
    if bracket is None:
        return fixture.home_team, fixture.away_team
    home, away = bracket.resolved_teams.get(fixture.match_number, (None, None))
    return home or fixture.home_team, away or fixture.away_team
