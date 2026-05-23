import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.client import HTTPConnection, HTTPResponse

from app.predictions import TEAM_PROFILES, is_known_team
from app.teams import TEAM_NAMES_NL
from app.tournament import build_tournament_view, load_fixtures
from app.webapp import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEPLOY_HOST,
    allowed_cors_origins,
    create_server,
    default_host,
    default_port,
    health_payload,
)

PICKS = {"1", "2", "3"}
PREDICTION_STATUSES = {"correct", "wrong", "pending"}
MATCH_STATUSES = {"completed", "upcoming"}
MATCH_STAGES = {"group", "knockout"}


def test_health_payload_identifies_backend() -> None:
    assert health_payload() == {"status": "ok", "service": "wk-pool-backend"}


def test_default_host_stays_local_without_platform_port(monkeypatch) -> None:
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)

    assert default_host() == DEFAULT_HOST


def test_default_host_binds_publicly_when_platform_port_exists(monkeypatch) -> None:
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.setenv("PORT", "54321")

    assert default_host() == DEPLOY_HOST
    assert default_port() == 54321


def test_default_port_uses_local_port_without_platform_port(monkeypatch) -> None:
    monkeypatch.delenv("PORT", raising=False)

    assert default_port() == DEFAULT_PORT


def test_allowed_cors_origins_reads_comma_separated_env(monkeypatch) -> None:
    monkeypatch.setenv("WK_POOL_ALLOWED_ORIGINS", "https://frontend.example, http://localhost:5173, ")

    assert allowed_cors_origins() == ("https://frontend.example", "http://localhost:5173")


def test_health_route_returns_json_with_security_headers_and_allowlisted_cors(monkeypatch) -> None:
    monkeypatch.setenv("WK_POOL_ALLOWED_ORIGINS", "https://frontend.example")

    response, body = get("/health", headers={"Origin": "https://frontend.example"})

    assert response.status == 200
    assert response.getheader("Content-Type") == "application/json; charset=utf-8"
    assert response.getheader("Access-Control-Allow-Origin") == "https://frontend.example"
    assert response.getheader("Vary") == "Origin"
    assert response.getheader("Content-Security-Policy") == "default-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    assert response.getheader("X-Content-Type-Options") == "nosniff"
    assert response.getheader("Referrer-Policy") == "no-referrer"
    assert json.loads(body) == health_payload()


def test_health_route_omits_cors_for_untrusted_origin(monkeypatch) -> None:
    monkeypatch.setenv("WK_POOL_ALLOWED_ORIGINS", "https://frontend.example")

    response, _body = get("/health", headers={"Origin": "https://evil.example"})

    assert response.status == 200
    assert response.getheader("Access-Control-Allow-Origin") is None


def test_tournament_route_serves_frontend_contract(monkeypatch) -> None:
    monkeypatch.setenv("WK_POOL_ALLOWED_ORIGINS", "https://frontend.example")

    response, body = get("/api/tournament", headers={"Origin": "https://frontend.example"})

    assert response.status == 200
    assert response.getheader("Access-Control-Allow-Methods") == "GET, OPTIONS"
    assert is_tournament_view(json.loads(body))


def test_options_route_returns_cors_preflight(monkeypatch) -> None:
    monkeypatch.setenv("WK_POOL_ALLOWED_ORIGINS", "https://frontend.example")

    response, body = request("OPTIONS", "/api/tournament", headers={"Origin": "https://frontend.example"})

    assert response.status == 204
    assert body == b""
    assert response.getheader("Access-Control-Allow-Origin") == "https://frontend.example"
    assert response.getheader("Access-Control-Allow-Headers") == "Content-Type"


def test_unknown_route_returns_404() -> None:
    response, body = get("/unknown")

    assert response.status == 404
    assert b"Not found" in body


def test_sync_football_requires_secret(monkeypatch) -> None:
    monkeypatch.delenv("FOOTBALL_SYNC_SECRET", raising=False)

    response, body = request("POST", "/internal/sync-football")

    assert response.status == 503
    assert b"FOOTBALL_SYNC_SECRET" in body


def test_sync_football_rejects_bad_token(monkeypatch) -> None:
    monkeypatch.setenv("FOOTBALL_SYNC_SECRET", "secret")
    monkeypatch.setenv("FOOTBALL_API_KEY", "key")

    response, _body = request(
        "POST",
        "/internal/sync-football",
        headers={"Authorization": "Bearer wrong"},
    )

    assert response.status == 401


def test_sync_football_triggers_sync(monkeypatch) -> None:
    monkeypatch.setenv("FOOTBALL_SYNC_SECRET", "secret")
    monkeypatch.setenv("FOOTBALL_API_KEY", "key")

    called: dict[str, bool] = {}

    def fake_sync(*, dry_run: bool = False, force_remap: bool = False) -> int:
        called["force_remap"] = force_remap
        return 2

    monkeypatch.setattr("app.football_sync.sync_results", fake_sync)

    response, body = request(
        "POST",
        "/internal/sync-football?force-remap=1",
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status == 200
    assert json.loads(body) == {"status": "ok", "synced": 2}
    assert called["force_remap"] is True


def test_load_fixtures_reads_world_cup_csv() -> None:
    fixtures = load_fixtures()

    assert len(fixtures) == 104
    assert fixtures[0].home_team == "Mexico"
    assert fixtures[0].away_team == "South Africa"
    assert fixtures[0].group == "A"


GROUP_STAGE_ROUND_LABELS = frozenset({"1", "2", "3"})
KNOCKOUT_ROUND_LABELS = frozenset(
    {"Round of 32", "Round of 16", "Quarter Finals", "Semi Finals", "Finals"},
)


def test_fixture_csv_schema_and_round_labels() -> None:
    fixtures = load_fixtures()
    numbers = [fixture.match_number for fixture in fixtures]
    assert numbers == list(range(1, len(fixtures) + 1))

    for fixture in fixtures:
        assert fixture.home_team.strip()
        assert fixture.away_team.strip()
        if fixture.group is not None:
            assert fixture.group in set("ABCDEFGHIJKL")
            assert fixture.round_number in GROUP_STAGE_ROUND_LABELS
        else:
            assert fixture.round_number in KNOCKOUT_ROUND_LABELS


def test_fixture_csv_known_teams_have_explicit_profiles() -> None:
    missing: list[str] = []
    for fixture in load_fixtures():
        for team in (fixture.home_team, fixture.away_team):
            if is_known_team(team) and team not in TEAM_PROFILES:
                missing.append(team)

    assert sorted(set(missing)) == []


def test_tournament_view_contains_pickem_preview() -> None:
    tournament = build_tournament_view()
    summary = tournament["summary"]

    assert summary["groupMatches"] == 72
    assert summary["completed"] == 0
    assert summary["upcoming"] == 104
    assert summary["aiCorrect"] == 0
    assert summary["aiWrong"] == 0
    assert summary["aiPending"] == 72
    assert len(tournament["groups"]) == 12


def test_tournament_preview_matches_are_chronological() -> None:
    tournament = build_tournament_view()

    assert tournament["nextMatch"]["matchNumber"] == 1
    assert [match["matchNumber"] for match in tournament["upcomingMatches"]] == [
        1,
        2,
        3,
        4,
        8,
        7,
        5,
        6,
    ]
    assert tournament["recentMatches"] == []


def test_tournament_view_uses_dutch_team_names() -> None:
    tournament = build_tournament_view()
    nl = TEAM_NAMES_NL["Netherlands"]
    all_matches = (
        tournament["recentMatches"]
        + tournament["upcomingMatches"]
        + [m for g in tournament["groups"] for m in g["matches"]]
    )
    match = next(
        m for m in all_matches if m["homeTeam"] == nl or m["awayTeam"] == nl
    )
    assert "Netherlands" not in (match["homeTeam"], match["awayTeam"])
    assert nl in tournament["teamInsights"]


def test_tournament_view_matches_frontend_contract() -> None:
    tournament = build_tournament_view()

    assert is_tournament_view(tournament)


def is_tournament_view(tournament: object) -> bool:
    assert isinstance(tournament, dict)
    assert_number_fields(
        tournament["summary"],
        [
            "totalMatches",
            "groupMatches",
            "completed",
            "upcoming",
            "aiCorrect",
            "aiWrong",
            "aiPending",
            "aiAccuracy",
        ],
    )
    assert tournament["nextMatch"] is None or is_match(tournament["nextMatch"])
    assert all(is_match(match) for match in tournament["recentMatches"])
    assert all(is_match(match) for match in tournament["upcomingMatches"])
    assert all(is_team_insight(insight) for insight in tournament["teamInsights"].values())

    for group in tournament["groups"]:
        assert isinstance(group["name"], str)
        assert all(is_standing(standing) for standing in group["standings"])
        assert all(is_match(match) for match in group["matches"])
        assert isinstance(group["predictedWinner"], str)
        assert group["winnerPredictionStatus"] in {"correct", "wrong", "pending"}

    assert all(is_match(match) for match in tournament["knockoutMatches"])
    assert is_crystal_ball(tournament["crystalBall"])
    return True


def is_crystal_ball(value: object) -> bool:
    if not isinstance(value, dict):
        return False

    group_winners = value.get("groupWinners")
    if not isinstance(group_winners, list):
        return False
    for entry in group_winners:
        if not isinstance(entry, dict):
            return False
        if not isinstance(entry.get("group"), str) or not isinstance(entry.get("team"), str):
            return False
        if entry.get("status") not in {"correct", "wrong", "pending"}:
            return False

    projected_groups = value.get("projectedGroups")
    if not isinstance(projected_groups, list):
        return False
    for group in projected_groups:
        if not isinstance(group, dict):
            return False
        if not isinstance(group.get("name"), str):
            return False
        if group.get("winner") is not None and not isinstance(group.get("winner"), str):
            return False
        standings = group.get("standings")
        if not isinstance(standings, list) or not all(is_standing(standing) for standing in standings):
            return False

    bonus_questions = value.get("bonusQuestions")
    if not isinstance(bonus_questions, list):
        return False
    for question in bonus_questions:
        if not isinstance(question, dict):
            return False
        if not all(isinstance(question.get(key), str) for key in ("id", "label", "value", "helper")):
            return False

    sources = value.get("sources")
    if not isinstance(sources, list) or not all(isinstance(source, str) for source in sources):
        return False

    if not isinstance(value.get("contextAsOf"), str):
        return False

    live_stats = value.get("liveStats")
    if not isinstance(live_stats, dict):
        return False
    if live_stats.get("source") != "api-football":
        return False
    updated_at = live_stats.get("updatedAt")
    if updated_at is not None and not isinstance(updated_at, str):
        return False
    for key in ("completedMatches", "totalMatches", "yellowCards", "directRedCards"):
        if not is_int(live_stats.get(key)):
            return False

    top_scorer = live_stats.get("topScorer")
    if top_scorer is not None:
        if not isinstance(top_scorer, dict):
            return False
        if not isinstance(top_scorer.get("name"), str):
            return False
        if not is_int(top_scorer.get("goals")):
            return False
        if not isinstance(top_scorer.get("team"), str):
            return False

    return True


def get(path: str, headers: dict[str, str] | None = None) -> tuple[HTTPResponse, bytes]:
    return request("GET", path, headers=headers)


def request(method: str, path: str, headers: dict[str, str] | None = None) -> tuple[HTTPResponse, bytes]:
    with running_server() as (host, port):
        connection = HTTPConnection(host, port, timeout=2)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            body = response.read()
        finally:
            connection.close()

    return response, body


@contextmanager
def running_server() -> Iterator[tuple[str, int]]:
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def is_match(value: object) -> bool:
    if not isinstance(value, dict):
        return False

    return (
        is_number(value.get("matchNumber"))
        and isinstance(value.get("round"), str)
        and value.get("stage") in MATCH_STAGES
        and (isinstance(value.get("group"), str) or value.get("group") is None)
        and isinstance(value.get("kickoffAt"), str)
        and isinstance(value.get("location"), str)
        and isinstance(value.get("homeTeam"), str)
        and isinstance(value.get("awayTeam"), str)
        and value.get("status") in MATCH_STATUSES
        and (value.get("score") is None or is_score(value.get("score")))
        and (value.get("actualPick") is None or value.get("actualPick") in PICKS)
        and is_ai_prediction(value.get("aiPrediction"))
    )


def is_score(value: object) -> bool:
    return isinstance(value, dict) and is_int(value.get("home")) and is_int(value.get("away"))


def is_ai_prediction(value: object) -> bool:
    if not isinstance(value, dict):
        return False

    base = (
        value.get("pick") in PICKS
        and is_number(value.get("confidence"))
        and isinstance(value.get("explanation"), str)
        and value.get("status") in PREDICTION_STATUSES
        and (value.get("homeWinProbability") is None or is_number(value.get("homeWinProbability")))
        and (value.get("drawProbability") is None or is_number(value.get("drawProbability")))
        and (value.get("awayWinProbability") is None or is_number(value.get("awayWinProbability")))
    )
    if not base:
        return False
    if value.get("confidence", 0) > 0:
        return is_prediction_insight(value.get("insight"))
    return value.get("insight") is None


def is_prediction_insight(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    steps = value.get("steps")
    steps_ok = steps is None or (
        isinstance(steps, list)
        and all(
            isinstance(step, dict)
            and isinstance(step.get("title"), str)
            and isinstance(step.get("body"), str)
            for step in steps
        )
    )
    narrative_ok = value.get("narrative") is None or isinstance(value.get("narrative"), str)
    return (
        isinstance(value.get("scoreSummary"), str)
        and isinstance(value.get("verdict"), str)
        and narrative_ok
        and steps_ok
        and isinstance(value.get("tags"), list)
        and is_number(value.get("diff"))
        and isinstance(value.get("home"), dict)
        and isinstance(value.get("away"), dict)
    )


def is_team_insight(value: object) -> bool:
    if not isinstance(value, dict):
        return False

    niche_ok = value.get("niche") is None or is_string_list(value.get("niche"))
    opponents_ok = value.get("opponents") is None or is_string_list(value.get("opponents"))
    return (
        isinstance(value.get("team"), str)
        and isinstance(value.get("tier"), str)
        and isinstance(value.get("style"), str)
        and is_string_list(value.get("strengths"))
        and is_string_list(value.get("risks"))
        and isinstance(value.get("summary"), str)
        and niche_ok
        and opponents_ok
        and (value.get("powerScore") is None or is_number(value.get("powerScore")))
        and (value.get("group") is None or isinstance(value.get("group"), str))
        and (value.get("groupContext") is None or is_string_list(value.get("groupContext")))
        and (value.get("distinctiveSpark") is None or isinstance(value.get("distinctiveSpark"), str))
    )


def is_standing(value: object) -> bool:
    return isinstance(value, dict) and isinstance(value.get("team"), str) and assert_number_fields(
        value,
        ["played", "wins", "draws", "losses", "goalsFor", "goalsAgainst", "goalDifference", "points"],
    )


def is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def assert_number_fields(value: object, fields: list[str]) -> bool:
    assert isinstance(value, dict)
    for field in fields:
        assert is_number(value.get(field))
    return True
