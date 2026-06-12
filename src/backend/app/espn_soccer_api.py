"""ESPN public soccer API — free 2026 World Cup scores, cards, and goals."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.tournament import Fixture

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
TOURNAMENT_START = datetime(2026, 6, 11, tzinfo=timezone.utc)

# Local CSV name → ESPN displayName variants (both directions resolve via canonical).
TEAM_CANONICAL: dict[str, str] = {
    "Korea Republic": "korea republic",
    "South Korea": "korea republic",
    "Czechia": "czechia",
    "Czech Republic": "czechia",
    "Bosnia and Herzegovina": "bosnia and herzegovina",
    "Bosnia-Herzegovina": "bosnia and herzegovina",
    "Côte d'Ivoire": "ivory coast",
    "Ivory Coast": "ivory coast",
    "IR Iran": "iran",
    "Iran": "iran",
    "Türkiye": "turkey",
    "Turkey": "turkey",
    "Cabo Verde": "cape verde",
    "Cape Verde": "cape verde",
}


def _canonical_team(name: str) -> str:
    return TEAM_CANONICAL.get(name, name.casefold())


def teams_match(local_home: str, local_away: str, event: dict[str, object]) -> bool:
    competition = _competition(event)
    if competition is None:
        return False

    espn_home = espn_away = None
    competitors = competition.get("competitors")
    if not isinstance(competitors, list):
        return False

    for competitor in competitors:
        if not isinstance(competitor, dict):
            continue
        team = competitor.get("team")
        if not isinstance(team, dict):
            continue
        display_name = str(team.get("displayName", ""))
        if competitor.get("homeAway") == "home":
            espn_home = display_name
        elif competitor.get("homeAway") == "away":
            espn_away = display_name

    if not espn_home or not espn_away:
        return False

    return (
        _canonical_team(local_home) == _canonical_team(espn_home)
        and _canonical_team(local_away) == _canonical_team(espn_away)
    )


def _competition(event: dict[str, object]) -> dict[str, object] | None:
    competitions = event.get("competitions")
    if not isinstance(competitions, list) or not competitions:
        return None
    first = competitions[0]
    return first if isinstance(first, dict) else None


def is_finished(event: dict[str, object]) -> bool:
    competition = _competition(event)
    if competition is None:
        return False

    status = competition.get("status")
    if not isinstance(status, dict):
        return False

    status_type = status.get("type")
    if not isinstance(status_type, dict):
        return False

    return status_type.get("state") == "post" and bool(status_type.get("completed"))


def fetch_scoreboard(*, date: str) -> list[dict[str, object]]:
    """Fetch scoreboard for one day. ``date`` is YYYYMMDD."""
    url = f"{BASE_URL}?{urlencode({'dates': date})}"
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    events = payload.get("events")
    return events if isinstance(events, list) else []


def fetch_scoreboards_for_dates(dates: set[str]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for date in sorted(dates):
        for event in fetch_scoreboard(date=date):
            if isinstance(event, dict):
                events.append(event)
    return events


def tournament_dates_through(now: datetime) -> set[str]:
    dates: set[str] = set()
    day = TOURNAMENT_START.date()
    while day <= now.date():
        dates.add(day.strftime("%Y%m%d"))
        day = day.fromordinal(day.toordinal() + 1)
    return dates


def match_espn_event(fixture: Fixture, events: list[dict[str, object]]) -> dict[str, object] | None:
    kickoff_key = fixture.kickoff_at.strftime("%Y-%m-%dT%H:%M")
    for event in events:
        if not isinstance(event, dict):
            continue
        if not teams_match(fixture.home_team, fixture.away_team, event):
            continue
        event_date = str(event.get("date", ""))
        if event_date.startswith(kickoff_key):
            return event
    for event in events:
        if isinstance(event, dict) and teams_match(fixture.home_team, fixture.away_team, event):
            return event
    return None


def _player_key(detail: dict[str, object]) -> str:
    athletes = detail.get("athletesInvolved")
    if not isinstance(athletes, list) or not athletes:
        return ""
    athlete = athletes[0]
    if not isinstance(athlete, dict):
        return ""
    athlete_id = athlete.get("id")
    if athlete_id is not None:
        return f"id:{athlete_id}"
    name = athlete.get("displayName")
    return f"name:{name}" if name else ""


def count_espn_cards(details: list[dict[str, object]]) -> tuple[int, int]:
    """Return (yellow_cards, direct_red_cards) using pool rules."""
    yellow_cards = 0
    direct_red_cards = 0
    yellows_by_player: dict[str, int] = {}

    for detail in details:
        if not isinstance(detail, dict):
            continue

        if detail.get("yellowCard"):
            yellow_cards += 1
            player = _player_key(detail)
            if player:
                yellows_by_player[player] = yellows_by_player.get(player, 0) + 1
            continue

        if not detail.get("redCard"):
            continue

        player = _player_key(detail)
        prior_yellows = yellows_by_player.get(player, 0) if player else 0
        if prior_yellows == 0:
            direct_red_cards += 1

    return yellow_cards, direct_red_cards


def parse_espn_result(event: dict[str, object]) -> dict[str, object] | None:
    if not is_finished(event):
        return None

    competition = _competition(event)
    if competition is None:
        return None

    home_score = away_score = None
    competitors = competition.get("competitors")
    if not isinstance(competitors, list):
        return None

    for competitor in competitors:
        if not isinstance(competitor, dict):
            continue
        score_raw = competitor.get("score")
        if score_raw is None:
            return None
        score = int(score_raw)
        if competitor.get("homeAway") == "home":
            home_score = score
        elif competitor.get("homeAway") == "away":
            away_score = score

    if home_score is None or away_score is None:
        return None

    details = competition.get("details")
    card_details = details if isinstance(details, list) else []
    yellow_cards, direct_red_cards = count_espn_cards(
        [entry for entry in card_details if isinstance(entry, dict)]
    )

    status = competition.get("status")
    status_short = None
    if isinstance(status, dict):
        status_type = status.get("type")
        if isinstance(status_type, dict) and status_type.get("shortDetail"):
            status_short = str(status_type["shortDetail"])

    return {
        "apiFixtureId": event.get("id"),
        "statusShort": status_short or "FT",
        "score": {"home": home_score, "away": away_score},
        "yellowCards": yellow_cards,
        "directRedCards": direct_red_cards,
    }


def top_scorer_from_events(events: list[dict[str, object]]) -> dict[str, object] | None:
    tallies: dict[str, dict[str, object]] = {}

    for event in events:
        if not is_finished(event):
            continue
        competition = _competition(event)
        if competition is None:
            continue

        team_names: dict[str, str] = {}
        competitors = competition.get("competitors")
        if isinstance(competitors, list):
            for competitor in competitors:
                if not isinstance(competitor, dict):
                    continue
                team = competitor.get("team")
                if not isinstance(team, dict):
                    continue
                team_id = team.get("id")
                display_name = team.get("displayName")
                if team_id is not None and display_name:
                    team_names[str(team_id)] = str(display_name)

        details = competition.get("details")
        if not isinstance(details, list):
            continue

        for detail in details:
            if not isinstance(detail, dict) or not detail.get("scoringPlay"):
                continue
            athletes = detail.get("athletesInvolved")
            if not isinstance(athletes, list) or not athletes:
                continue
            athlete = athletes[0]
            if not isinstance(athlete, dict):
                continue
            name = athlete.get("displayName")
            if not name:
                continue
            team_meta = detail.get("team")
            team_name = ""
            if isinstance(team_meta, dict) and team_meta.get("id") is not None:
                team_name = team_names.get(str(team_meta["id"]), "")

            key = str(name)
            entry = tallies.setdefault(key, {"name": str(name), "goals": 0, "team": team_name})
            entry["goals"] = int(entry["goals"]) + 1
            if team_name:
                entry["team"] = team_name

    if not tallies:
        return None

    return max(tallies.values(), key=lambda row: int(row["goals"]))
