"""API-Sports / API-Football client and match result parsing."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://v3.football.api-sports.io"
WORLD_CUP_LEAGUE_ID = 1
API_KEY_ENV_NAMES = ("FOOTBALL_API_KEY", "API_FOOTBALL_KEY")
FINISHED_STATUS_SHORT = frozenset({"FT", "AET", "PEN"})
LIVE_STATUS_SHORT = frozenset({"1H", "HT", "2H", "ET", "BT", "P", "LIVE"})

# CSV / display name → API team name when they differ.
TEAM_API_ALIASES: dict[str, str] = {
    "Côte d'Ivoire": "Ivory Coast",
    "IR Iran": "Iran",
}


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
            continue
        key, value = clean_line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def api_key() -> str | None:
    load_env_file()
    for name in API_KEY_ENV_NAMES:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def call_api_football(path: str, params: dict[str, str | int]) -> dict[str, object]:
    key = api_key()
    if not key:
        raise RuntimeError(f"Missing env var: one of {', '.join(API_KEY_ENV_NAMES)}")

    url = f"{BASE_URL}{path}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "x-apisports-key": key,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def api_team_name(team: str) -> str:
    return TEAM_API_ALIASES.get(team, team)


def _player_key(event: dict[str, object]) -> str:
    player = event.get("player")
    if not isinstance(player, dict):
        return ""
    player_id = player.get("id")
    if player_id is not None:
        return f"id:{player_id}"
    name = player.get("name")
    return f"name:{name}" if name else ""


def count_card_events(events: list[dict[str, object]]) -> tuple[int, int]:
    """Return (yellow_cards, direct_red_cards) for pool rules."""
    yellow_cards = 0
    direct_red_cards = 0
    yellows_by_player: dict[str, int] = {}

    for event in events:
        if str(event.get("type")) != "Card":
            continue

        detail = str(event.get("detail", ""))
        player = _player_key(event)

        if detail == "Yellow Card":
            yellow_cards += 1
            if player:
                yellows_by_player[player] = yellows_by_player.get(player, 0) + 1
            continue

        if detail == "Yellow Red Card":
            yellow_cards += 1
            continue

        if detail != "Red Card":
            continue

        prior_yellows = yellows_by_player.get(player, 0) if player else 0
        if prior_yellows < 2:
            direct_red_cards += 1

    return yellow_cards, direct_red_cards


def regulation_score(fixture: dict[str, object]) -> tuple[int, int] | None:
    """Score at end of 90 minutes (+ stoppage), before extra time."""
    goals = fixture.get("goals")
    score = fixture.get("score")
    if not isinstance(goals, dict):
        return None

    home = goals.get("home")
    away = goals.get("away")
    if home is None or away is None:
        return None

    fixture_meta = fixture.get("fixture")
    status_short = ""
    if isinstance(fixture_meta, dict):
        status = fixture_meta.get("status")
        if isinstance(status, dict):
            status_short = str(status.get("short", ""))

    if status_short in {"AET", "PEN"} and isinstance(score, dict):
        fulltime = score.get("fulltime")
        if isinstance(fulltime, dict):
            ft_home = fulltime.get("home")
            ft_away = fulltime.get("away")
            if ft_home is not None and ft_away is not None:
                return int(ft_home), int(ft_away)

    if isinstance(score, dict):
        fulltime = score.get("fulltime")
        if isinstance(fulltime, dict):
            ft_home = fulltime.get("home")
            ft_away = fulltime.get("away")
            if ft_home is not None and ft_away is not None:
                return int(ft_home), int(ft_away)

    return int(home), int(away)


def is_finished(fixture: dict[str, object]) -> bool:
    fixture_meta = fixture.get("fixture")
    if not isinstance(fixture_meta, dict):
        return False
    status = fixture_meta.get("status")
    if not isinstance(status, dict):
        return False
    return str(status.get("short", "")) in FINISHED_STATUS_SHORT


def parse_fixture_result(fixture: dict[str, object]) -> dict[str, object] | None:
    if not is_finished(fixture):
        return None

    score = regulation_score(fixture)
    if score is None:
        return None

    events = fixture.get("events")
    if not isinstance(events, list):
        events = []

    yellow_cards, direct_red_cards = count_card_events(events)
    fixture_meta = fixture.get("fixture")
    fixture_id = fixture_meta.get("id") if isinstance(fixture_meta, dict) else None
    status = fixture_meta.get("status") if isinstance(fixture_meta, dict) else {}
    status_short = status.get("short") if isinstance(status, dict) else None

    return {
        "apiFixtureId": fixture_id,
        "statusShort": status_short,
        "score": {"home": score[0], "away": score[1]},
        "yellowCards": yellow_cards,
        "directRedCards": direct_red_cards,
    }


def fetch_fixtures_by_ids(fixture_ids: list[int]) -> list[dict[str, object]]:
    if not fixture_ids:
        return []

    chunks: list[list[int]] = []
    for index in range(0, len(fixture_ids), 20):
        chunks.append(fixture_ids[index : index + 20])

    fixtures: list[dict[str, object]] = []
    for chunk in chunks:
        ids_param = "-".join(str(fixture_id) for fixture_id in chunk)
        data = call_api_football("/fixtures", {"ids": ids_param})
        response = data.get("response", [])
        if isinstance(response, list):
            fixtures.extend(response)
    return fixtures


def fetch_league_fixtures(season: int) -> list[dict[str, object]]:
    data = call_api_football(
        "/fixtures",
        {"league": WORLD_CUP_LEAGUE_ID, "season": season},
    )
    response = data.get("response", [])
    return response if isinstance(response, list) else []


def fetch_top_scorers(season: int) -> list[dict[str, object]]:
    data = call_api_football(
        "/players/topscorers",
        {"league": WORLD_CUP_LEAGUE_ID, "season": season},
    )
    response = data.get("response", [])
    return response if isinstance(response, list) else []


def parse_top_scorer(entries: list[dict[str, object]]) -> dict[str, object] | None:
    """Return leading tournament scorer from /players/topscorers response."""
    best: dict[str, object] | None = None
    best_goals = -1

    for entry in entries:
        player = entry.get("player")
        statistics = entry.get("statistics")
        if not isinstance(player, dict) or not isinstance(statistics, list) or not statistics:
            continue

        stats = statistics[0]
        if not isinstance(stats, dict):
            continue

        goals_meta = stats.get("goals")
        if not isinstance(goals_meta, dict):
            continue

        total = goals_meta.get("total")
        if total is None:
            continue

        goals = int(total)
        if goals <= best_goals:
            continue

        team_meta = stats.get("team")
        team_name = ""
        if isinstance(team_meta, dict) and team_meta.get("name") is not None:
            team_name = str(team_meta["name"])

        name = player.get("name")
        if not name:
            continue

        best_goals = goals
        best = {
            "name": str(name),
            "goals": goals,
            "team": team_name,
        }

    return best


def match_api_fixture(
    *,
    kickoff_iso: str,
    home_team: str,
    away_team: str,
    api_fixtures: list[dict[str, object]],
) -> dict[str, object] | None:
    kickoff_prefix = kickoff_iso[:16]
    home_api = api_team_name(home_team)
    away_api = api_team_name(away_team)

    for fixture in api_fixtures:
        fixture_meta = fixture.get("fixture")
        teams = fixture.get("teams")
        if not isinstance(fixture_meta, dict) or not isinstance(teams, dict):
            continue

        date = str(fixture_meta.get("date", ""))
        if not date.startswith(kickoff_prefix[:10]):
            continue

        home = teams.get("home", {})
        away = teams.get("away", {})
        if not isinstance(home, dict) or not isinstance(away, dict):
            continue

        if home.get("name") == home_api and away.get("name") == away_api:
            return fixture

    return None
