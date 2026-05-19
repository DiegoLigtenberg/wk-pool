"""Groepsfase-kalender uit FIFA CSV: fixture-hooks en rust/reis tussen wedstrijden."""

from __future__ import annotations

import csv

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from app.data.teams.team_bundle import GroupFixture, GroupStage
from app.teams import display_team_name, localize_teams_in_text

CSV_PATH = Path(__file__).resolve().parents[1] / "fifa-world-cup-2026-UTC.csv"

# Bekende narratieven (niet elk team) ,  uitbreidbaar.
NOTABLE_FIXTURE_NARRATIVES: dict[tuple[str, str], str] = {
    ("Brazil", "Morocco"): "Rematch WK 2022 halve finale",
    ("Morocco", "Brazil"): "Rematch WK 2022 halve finale",
    ("Argentina", "Algeria"): "Groeps-opener titelverdediger vs Algerije",
    ("Algeria", "Argentina"): "Meteen tegen titelverdediger Argentinië",
    ("USA", "Paraguay"): "Co-host opener vs Paraguay",
    ("Paraguay", "USA"): "Uit tegen co-host USA",
    ("Canada", "Bosnia and Herzegovina"): "Co-host opener vs Bosnië",
    ("Mexico", "South Africa"): "Co-host opener (Mexico City)",
    ("South Africa", "Mexico"): "Opener op ≈2240m vs co-host Mexico",
    ("France", "Senegal"): "Groep I-opener vs Senegal",
    ("England", "Croatia"): "Groep L: Engeland, Kroatië",
    ("Netherlands", "Japan"): "Groep F-opener; Nederland zonder Xavi Simons (knie)",
    ("Japan", "Netherlands"): "Japan zet hoog druk aan; Nederland begint vaak compact",
}


@dataclass(frozen=True, slots=True)
class GroupMatch:
    kickoff: datetime
    location: str
    home_team: str
    away_team: str
    group: str
    is_home: bool
    opponent: str


def _parse_group_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["Group"].startswith("Group "):
                rows.append(row)
    return rows


@lru_cache(maxsize=1)
def _matches_by_team() -> dict[str, list[GroupMatch]]:
    by_team: dict[str, list[GroupMatch]] = {}
    for row in _parse_group_rows():
        kickoff = datetime.strptime(row["Date"], "%d/%m/%Y %H:%M")
        location = row["Location"].strip()
        group = row["Group"].removeprefix("Group ").strip()
        home = row["Home Team"].strip()
        away = row["Away Team"].strip()
        for team, opp, is_home in ((home, away, True), (away, home, False)):
            by_team.setdefault(team, []).append(
                GroupMatch(
                    kickoff=kickoff,
                    location=location,
                    home_team=home,
                    away_team=away,
                    group=group,
                    is_home=is_home,
                    opponent=opp,
                )
            )
    for team in by_team:
        by_team[team].sort(key=lambda m: m.kickoff)
    return by_team


def build_group_fixture_hooks(team_id: str) -> list[str]:
    matches = _matches_by_team().get(team_id, [])
    if not matches:
        return []

    hooks: list[str] = []
    group = matches[0].group
    opponents = sorted({display_team_name(m.opponent) for m in matches})
    hooks.append(f"Groep {group}: tegen {', '.join(opponents)}.")

    for i, m in enumerate(matches, start=1):
        ha = "thuis" if m.is_home else "uit"
        opp = display_team_name(m.opponent)
        label = f"Groepswedstrijd {i} ({m.kickoff.strftime('%d %b')}): {ha} vs {opp} @ {m.location}"
        narrative = NOTABLE_FIXTURE_NARRATIVES.get((team_id, m.opponent))
        if narrative:
            label = f"{label}: {localize_teams_in_text(narrative)}"
        hooks.append(label)

    return hooks


def build_schedule_rest_notes(team_id: str) -> str | None:
    matches = _matches_by_team().get(team_id, [])
    if len(matches) < 2:
        return None

    parts: list[str] = []
    rests: list[int] = []
    for prev, curr in zip(matches, matches[1:]):
        delta_days = (curr.kickoff.date() - prev.kickoff.date()).days
        rests.append(delta_days)
        if prev.location != curr.location:
            parts.append(
                f"Tussen wedstrijd {display_team_name(prev.opponent)} en {display_team_name(curr.opponent)}: "
                f"{prev.location} → {curr.location} ({delta_days} dag(en) ertussen)."
            )

    if rests:
        min_rest = min(rests)
        parts.insert(
            0,
            f"Rust tussen groepswedstrijden: {min_rest}, {max(rests)} dag(en); "
            f"kortste window {'≤3' if min_rest <= 3 else '>3'} dagen.",
        )

    late = sum(
        1
        for m in matches
        if m.kickoff.hour <= 4 or (m.kickoff.hour == 4 and m.kickoff.minute == 0)
    )
    if late >= 2:
        parts.append(f"{late} vroege/late kickoff-slots (UTC-nacht) in groep, recovery relevant.")

    if not parts:
        return None
    return " ".join(parts)


def group_stage_for_team(team_id: str) -> GroupStage:
    """Gestructureerde groepsfase uit CSV (fallback als YAML geen group_stage heeft)."""
    matches = _matches_by_team().get(team_id, [])
    if not matches:
        raise ValueError(f"No group fixtures in CSV for {team_id!r}")

    fixtures: list[GroupFixture] = []
    for i, m in enumerate(matches, start=1):
        narrative = NOTABLE_FIXTURE_NARRATIVES.get((team_id, m.opponent))
        fixtures.append(
            GroupFixture(
                match_number=i,
                kickoff=m.kickoff.strftime("%Y-%m-%dT%H:%M"),
                is_home=m.is_home,
                opponent_fifa=m.opponent,
                opponent_nl=display_team_name(m.opponent),
                stadium=m.location,
                narrative=localize_teams_in_text(narrative) if narrative else None,
            )
        )

    from app.data.teams.fixture_venues import build_team_venue_notes

    return GroupStage(
        group=matches[0].group,
        opponents_nl=tuple(sorted({display_team_name(m.opponent) for m in matches})),
        opponents_fifa=tuple(sorted({m.opponent for m in matches})),
        fixtures=tuple(fixtures),
        fixture_hooks=tuple(build_group_fixture_hooks(team_id)),
        schedule_rest_notes=build_schedule_rest_notes(team_id),
        venue_dispersion_notes=build_team_venue_notes(team_id),
    )
