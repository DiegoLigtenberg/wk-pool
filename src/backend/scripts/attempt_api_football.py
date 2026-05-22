"""Probe API-Football (api-sports.io): fixtures, scores, and card events."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://v3.football.api-sports.io"
WORLD_CUP_LEAGUE_ID = 1
API_KEY_ENV_NAMES = ("FOOTBALL_API_KEY", "API_FOOTBALL_KEY")


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


def api_key() -> str:
    load_env_file()
    for name in API_KEY_ENV_NAMES:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    raise RuntimeError(f"Missing env var: one of {', '.join(API_KEY_ENV_NAMES)}")


def call_api_football(path: str, params: dict[str, str | int]) -> dict[str, object]:
    url = f"{BASE_URL}{path}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "x-apisports-key": api_key(),
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fixture_label(fixture: dict[str, object]) -> str:
    teams = fixture.get("teams", {})
    if not isinstance(teams, dict):
        return "unknown fixture"
    home = teams.get("home", {})
    away = teams.get("away", {})
    home_name = home.get("name", "?") if isinstance(home, dict) else "?"
    away_name = away.get("name", "?") if isinstance(away, dict) else "?"
    goals = fixture.get("goals", {})
    if isinstance(goals, dict):
        return f"{home_name} {goals.get('home')}-{goals.get('away')} {away_name}"
    return f"{home_name} vs {away_name}"


def card_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
    cards: list[dict[str, object]] = []
    for event in events:
        if str(event.get("type")) != "Card":
            continue
        cards.append(
            {
                "minute": event.get("time", {}).get("elapsed") if isinstance(event.get("time"), dict) else None,
                "detail": event.get("detail"),
                "player": event.get("player", {}).get("name") if isinstance(event.get("player"), dict) else None,
                "team": event.get("team", {}).get("name") if isinstance(event.get("team"), dict) else None,
            }
        )
    return cards


def team_card_totals(fixture_id: int) -> list[str]:
    stats_data = call_api_football("/fixtures/statistics", {"fixture": fixture_id})
    stats = stats_data.get("response", [])
    lines: list[str] = []
    if not isinstance(stats, list):
        return lines

    for team_stats in stats:
        team_name = team_stats.get("team", {}).get("name") if isinstance(team_stats.get("team"), dict) else "?"
        yellow = red = None
        for stat in team_stats.get("statistics", []) if isinstance(team_stats.get("statistics"), list) else []:
            if stat.get("type") == "Yellow Cards":
                yellow = stat.get("value")
            if stat.get("type") == "Red Cards":
                red = stat.get("value")
        lines.append(f"  team totals: {team_name} yellow={yellow} red={red}")
    return lines


def print_fixture_probe(fixture: dict[str, object]) -> None:
    fixture_meta = fixture.get("fixture", {})
    fixture_id = fixture_meta.get("id") if isinstance(fixture_meta, dict) else None
    round_name = fixture.get("league", {}).get("round") if isinstance(fixture.get("league"), dict) else None
    print(f"\n--- fixture {fixture_id} | {round_name} | {fixture_label(fixture)} ---")

    if not isinstance(fixture_id, int):
        return

    events_data = call_api_football("/fixtures/events", {"fixture": fixture_id})
    events = events_data.get("response", [])
    if not isinstance(events, list):
        events = []

    cards = card_events(events)
    print(f"card events ({len(cards)}):")
    for card in cards:
        print(f"  {card['minute']}' | {card['detail']} | {card['player']} ({card['team']})")

    for line in team_card_totals(fixture_id):
        print(line)


def find_fixture(
    fixtures: list[dict[str, object]],
    *,
    home: str,
    away: str,
) -> dict[str, object] | None:
    for fixture in fixtures:
        teams = fixture.get("teams", {})
        if not isinstance(teams, dict):
            continue
        home_team = teams.get("home", {})
        away_team = teams.get("away", {})
        if not isinstance(home_team, dict) or not isinstance(away_team, dict):
            continue
        if home_team.get("name") == home and away_team.get("name") == away:
            return fixture
    return None


def find_team_fixture(
    fixtures: list[dict[str, object]],
    *,
    team: str,
    round_contains: str,
) -> dict[str, object] | None:
    for fixture in fixtures:
        teams = fixture.get("teams", {})
        league = fixture.get("league", {})
        if not isinstance(teams, dict) or not isinstance(league, dict):
            continue
        round_name = str(league.get("round", ""))
        if round_contains not in round_name:
            continue
        home = teams.get("home", {})
        away = teams.get("away", {})
        if not isinstance(home, dict) or not isinstance(away, dict):
            continue
        if team in (home.get("name"), away.get("name")):
            return fixture
    return None


def main() -> int:
    try:
        print("=== WC 2026 schedule probe ===")
        wc2026 = call_api_football(
            "/fixtures",
            {"league": WORLD_CUP_LEAGUE_ID, "season": 2026},
        )
        response2026 = wc2026.get("response", [])
        print(f"errors: {wc2026.get('errors')}")
        print(f"fixture count: {len(response2026) if isinstance(response2026, list) else 0}")
        if isinstance(response2026, list) and response2026:
            for fixture in response2026[:3]:
                print(f"  {fixture_label(fixture)}")

        print("\n=== WC 2022 finished fixtures ===")
        wc2022 = call_api_football(
            "/fixtures",
            {"league": WORLD_CUP_LEAGUE_ID, "season": 2022, "status": "FT"},
        )
        fixtures = wc2022.get("response", [])
        if not isinstance(fixtures, list):
            fixtures = []
        print(f"errors: {wc2022.get('errors')}")
        print(f"finished fixtures returned: {len(fixtures)}")

        samples = [
            find_team_fixture(fixtures, team="Netherlands", round_contains="Round of 16"),
            find_fixture(fixtures, home="Morocco", away="Portugal"),
        ]
        for fixture in samples:
            if fixture is None:
                continue
            print_fixture_probe(fixture)
            time.sleep(1)

        print("\nAPI card detail values to expect:")
        print("  Yellow Card | Red Card | Yellow Red Card (second booking in same match)")

    except RuntimeError as error:
        print(error)
        print("Set FOOTBALL_API_KEY in src/backend/.env")
        return 2
    except HTTPError as error:
        print(f"HTTP {error.code}: {error.reason}")
        print(error.read().decode("utf-8"))
        return 1
    except URLError as error:
        print(f"Request failed: {error.reason}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
