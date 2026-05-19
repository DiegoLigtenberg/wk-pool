"""Groepsfase-stadions en locatie-impact per team (uit FIFA CSV + vaste stadionprofielen)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "fifa-world-cup-2026-UTC.csv"


@dataclass(frozen=True, slots=True)
class StadiumProfile:
    city: str
    country: str
    climate_tag: str
    altitude_m: int | None = None
    note: str | None = None


# Vaste profielen voor pool-uitleg (niet live weer ,  stabiele context).
STADIUM_PROFILES: dict[str, StadiumProfile] = {
    "Mexico City Stadium": StadiumProfile(
        "Mexico City", "Mexico", "hoogte + warm", 2240,
        "Azteca-achtige hoogte; longballs en sprintherstel anders dan op zee-niveau.",
    ),
    "Guadalajara Stadium": StadiumProfile(
        "Guadalajara", "Mexico", "gematigd-hoog", 1560,
        "Iets koeler dan Mexico-Stad maar nog merkbare hoogte.",
    ),
    "Monterrey Stadium": StadiumProfile(
        "Monterrey", "Mexico", "heet droog", 540,
        "Noord-Mexico hitte; avondwedstrijden helpen maar zomerwarmte blijft.",
    ),
    "Toronto Stadium": StadiumProfile(
        "Toronto", "Canada", "gematigd zomer", None,
        "Co-host hub; geen extreme hoogte, wel reis naar VS-poule-steden.",
    ),
    "BC Place Vancouver": StadiumProfile(
        "Vancouver", "Canada", "koeler kust", None,
        "Koelste Canadese host; overdekt stadion, minder hitte-stress.",
    ),
    "Los Angeles Stadium": StadiumProfile(
        "Los Angeles", "USA", "warm droog", None,
        "SoCal; weinig lucht vochtigheid maar middag/zomerhitte kan spelen.",
    ),
    "San Francisco Bay Area Stadium": StadiumProfile(
        "San Francisco", "USA", "mild kust", None,
        "Koeler dan binnenland; avondkickoffs vaak aangenaam.",
    ),
    "Boston Stadium": StadiumProfile(
        "Boston", "USA", "vochtig zomer", None,
        "Oostkust vochtigheid; loopvolume en rust tussen wedstrijden tellen.",
    ),
    "New York/New Jersey Stadium": StadiumProfile(
        "New York", "USA", "vochtig zomer", None,
        "Metropool; veel reizende fans, hitte+vocht combinatie.",
    ),
    "Philadelphia Stadium": StadiumProfile(
        "Philadelphia", "USA", "warm vochtig", None,
        "Mid-Atlantic zomer; vergelijkbaar met NY-route qua klimaat.",
    ),
    "Miami Stadium": StadiumProfile(
        "Miami", "USA", "heet vochtig", None,
        "Tropisch; grootste hitte/hitte-index risico in groep H/I-finale-route.",
    ),
    "Houston Stadium": StadiumProfile(
        "Houston", "USA", "heet vochtig", None,
        "Gulf Coast; extreem vochtig, fysiek zwaar voor Europese kernen.",
    ),
    "Dallas Stadium": StadiumProfile(
        "Dallas", "USA", "heet droog", None,
        "Texas hitte; droger dan Houston maar hoge temperaturen.",
    ),
    "Kansas City Stadium": StadiumProfile(
        "Kansas City", "USA", "warm continentaal", None,
        "Binnenland; hitte+golfen vochtigheid in juni.",
    ),
    "Atlanta Stadium": StadiumProfile(
        "Atlanta", "USA", "heet vochtig", None,
        "Zuidoost VS; overdekt maar omgeving vochtig-warm.",
    ),
    "Seattle Stadium": StadiumProfile(
        "Seattle", "USA", "koel mild", None,
        "Pacific Northwest; koelste US-hosts, contrast met Miami/Houston.",
    ),
}


@dataclass(frozen=True, slots=True)
class TeamGroupVenues:
    team: str
    venues: tuple[str, ...]
    countries: tuple[str, ...]
    has_altitude: bool
    has_extreme_heat: bool
    has_cross_border: bool
    late_kickoffs: int  # local evening / after midnight UTC-ish slots


def _parse_group_stage_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if not row["Group"].startswith("Group "):
                continue
            rows.append(row)
    return rows


@lru_cache(maxsize=1)
def _team_group_venues() -> dict[str, TeamGroupVenues]:
    by_team: dict[str, list[str]] = {}
    late_by_team: dict[str, int] = {}

    for row in _parse_group_stage_rows():
        location = row["Location"].strip()
        for team in (row["Home Team"].strip(), row["Away Team"].strip()):
            if team == "To be announced":
                continue
            by_team.setdefault(team, []).append(location)
            kickoff = row["Date"]
            # 00:00, 04:00 UTC slots in CSV ≈ late local in US
            if any(kickoff.endswith(suffix) for suffix in (" 00:00", " 01:00", " 02:00", " 03:00", " 04:00")):
                late_by_team[team] = late_by_team.get(team, 0) + 1

    result: dict[str, TeamGroupVenues] = {}
    for team, venues in by_team.items():
        unique = tuple(dict.fromkeys(venues))
        profiles = [STADIUM_PROFILES[v] for v in unique if v in STADIUM_PROFILES]
        countries = tuple(dict.fromkeys(p.country for p in profiles))
        result[team] = TeamGroupVenues(
            team=team,
            venues=unique,
            countries=countries,
            has_altitude=any(p.altitude_m and p.altitude_m >= 1500 for p in profiles),
            has_extreme_heat=any(p.climate_tag in {"heet vochtig", "heet droog", "warm vochtig"} for p in profiles),
            has_cross_border=len(countries) > 1,
            late_kickoffs=late_by_team.get(team, 0),
        )
    return result


def build_team_venue_notes(team_id: str) -> str:
    """Natuurlijke taal over groepsfase-locaties + fysieke impact voor dit team."""
    info = _team_group_venues().get(team_id)
    if info is None:
        return (
            "Groepsfase-locaties niet gevonden in CSV; algemeen: 16 host-steden verspreid over "
            "Mexico, Canada en de VS met wisselende hitte, vochtigheid en enkele hoogte-venues."
        )

    venue_labels = []
    for name in info.venues:
        profile = STADIUM_PROFILES.get(name)
        if profile is None:
            venue_labels.append(name)
            continue
        if profile.altitude_m:
            venue_labels.append(f"{name} ({profile.city}, ≈{profile.altitude_m}m)")
        else:
            venue_labels.append(f"{name} ({profile.city}, {profile.climate_tag})")

    parts = [f"Groepsfase op {len(info.venues)} stadion{'s' if len(info.venues) > 1 else ''}: " + "; ".join(venue_labels) + "."]

    if len(info.countries) == 1:
        parts.append(f"Alleen {info.countries[0]}-venues in de poule, beperkte binnenlandse reis.")
    elif info.has_cross_border:
        parts.append(
            f"Cross-border poule ({', '.join(info.countries)}), extra vlucht/tijdzone tussen groepswedstrijden."
        )

    impacts: list[str] = []
    for name in info.venues:
        profile = STADIUM_PROFILES.get(name)
        if profile is None:
            continue
        if profile.altitude_m and profile.altitude_m >= 1500:
            impacts.append(
                f"{profile.city} (≈{profile.altitude_m}m) kan sprintherstel en balhang beïnvloeden"
            )
        elif profile.climate_tag in {"heet vochtig", "heet droog", "warm vochtig"}:
            impacts.append(f"{profile.city} ({profile.climate_tag}) vraagt hitte-management")
        elif profile.climate_tag in {"koeler kust", "koel mild", "mild kust"}:
            impacts.append(f"{profile.city} is koeler en kan hitte-gewende tegenstanders neutraliseren")

    if info.late_kickoffs >= 2:
        impacts.append(
            f"{info.late_kickoffs} late kickoffs in groep: rustritme en recovery extra relevant"
        )

    if impacts:
        parts.append("Impact: " + "; ".join(dict.fromkeys(impacts)) + ".")

    return " ".join(parts)
