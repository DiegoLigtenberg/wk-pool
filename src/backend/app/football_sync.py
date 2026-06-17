"""Sync finished match scores and cards into match-results.json."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from app.espn_soccer_api import (
    fetch_scoreboards_for_dates,
    match_espn_event,
    parse_espn_result,
    scoreboard_dates_for_fixtures,
    top_scorer_from_events,
    tournament_dates_through,
)
from app.football_api import (
    fetch_fixtures_by_ids,
    fetch_league_fixtures,
    fetch_top_scorers,
    match_api_fixture,
    parse_fixture_result,
    parse_top_scorer,
)
from app.match_results_store import (
    load_fixture_map,
    load_results,
    result_for_match,
    save_fixture_map,
    save_results,
    upsert_match_result,
)
from app.poll_schedule import MINUTES_AFTER_KICKOFF
from app.tournament import Fixture, load_fixtures


def default_season() -> int:
    return int(os.environ.get("FOOTBALL_API_SEASON", "2026"))


def data_provider() -> str:
    return os.environ.get("FOOTBALL_DATA_PROVIDER", "espn").strip().lower()


def live_stats_source() -> str:
    provider = data_provider()
    if provider in {"api-football", "apifootball", "api_football"}:
        return "api-football"
    return "espn"


def _ready_at(kickoff: datetime) -> datetime:
    return kickoff + timedelta(minutes=MINUTES_AFTER_KICKOFF)


def build_fixture_map(*, season: int, force: bool = False) -> dict[int, int]:
    existing = load_fixture_map()
    if existing and not force:
        return existing

    api_fixtures = fetch_league_fixtures(season)
    mapping: dict[int, int] = {}

    for fixture in load_fixtures():
        matched = match_api_fixture(
            kickoff_iso=fixture.kickoff_at.isoformat().replace("+00:00", "Z"),
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            api_fixtures=api_fixtures,
        )
        if matched is None:
            continue

        fixture_meta = matched.get("fixture")
        if isinstance(fixture_meta, dict) and fixture_meta.get("id") is not None:
            mapping[fixture.match_number] = int(fixture_meta["id"])

    if mapping:
        save_fixture_map(mapping)
        return mapping

    if force:
        print(f"Warning: mapped 0 fixtures for season {season}; fixture map not overwritten.")
    return existing


def _pending_fixtures(
    now: datetime,
    store: dict[str, object],
    *,
    require_fixture_map: bool,
    fixture_map: dict[int, int],
) -> list[Fixture]:
    pending: list[Fixture] = []
    for fixture in load_fixtures():
        if require_fixture_map and fixture.match_number not in fixture_map:
            continue
        if now < _ready_at(fixture.kickoff_at):
            continue
        if result_for_match(store, fixture.match_number) is not None:
            continue
        pending.append(fixture)
    return pending


def _completed_match_count(store: dict[str, object]) -> int:
    matches = store.get("matches")
    if not isinstance(matches, dict):
        return 0
    return len(matches)


def sync_top_scorer_api_football(store: dict[str, object], *, season: int, dry_run: bool = False) -> bool:
    if _completed_match_count(store) == 0:
        return False

    if dry_run:
        print("Would call /players/topscorers")
        return False

    parsed = parse_top_scorer(fetch_top_scorers(season))
    if parsed is None:
        return False

    existing = store.get("topScorer")
    if existing == parsed:
        return False

    store["topScorer"] = parsed
    print(f"Topscorer: {parsed['name']} ({parsed['goals']} goals, {parsed['team']})")
    return True


def sync_top_scorer_espn(
    store: dict[str, object],
    *,
    now: datetime,
    dry_run: bool = False,
) -> bool:
    if _completed_match_count(store) == 0:
        return False

    if dry_run:
        print("Would refresh topscorer from ESPN scoreboards")
        return False

    events = fetch_scoreboards_for_dates(tournament_dates_through(now))
    parsed = top_scorer_from_events(events)
    if parsed is None:
        return False

    existing = store.get("topScorer")
    if existing == parsed:
        return False

    store["topScorer"] = parsed
    print(f"Topscorer: {parsed['name']} ({parsed['goals']} goals, {parsed['team']})")
    return True


def sync_results(*, dry_run: bool = False, force_remap: bool = False) -> int:
    provider = data_provider()
    if provider in {"espn", "espn-soccer"}:
        return _sync_results_espn(dry_run=dry_run)
    if provider in {"api-football", "apifootball", "api_football"}:
        return _sync_results_api_football(dry_run=dry_run, force_remap=force_remap)
    raise RuntimeError(f"Unknown FOOTBALL_DATA_PROVIDER: {provider}")


def _sync_results_espn(*, dry_run: bool = False) -> int:
    now = datetime.now(timezone.utc)
    store = load_results()
    pending = _pending_fixtures(now, store, require_fixture_map=False, fixture_map={})

    if not pending:
        print("No newly finished matches to sync.")
        if sync_top_scorer_espn(store, now=now, dry_run=dry_run):
            save_results(store)
        return 0

    dates = scoreboard_dates_for_fixtures(pending)
    print(f"Syncing {len(pending)} match(es) via ESPN: {[f.match_number for f in pending]}")
    if dry_run:
        print(f"Would call ESPN scoreboard for {len(dates)} day(s)")
        return 0

    events = fetch_scoreboards_for_dates(dates)
    synced = 0
    for fixture in pending:
        event = match_espn_event(fixture, events)
        if event is None:
            print(f"  match {fixture.match_number}: no ESPN fixture for {fixture.home_team} vs {fixture.away_team}")
            continue

        parsed = parse_espn_result(event)
        if parsed is None:
            print(f"  match {fixture.match_number}: not finished yet")
            continue

        upsert_match_result(store, fixture.match_number, parsed)
        score = parsed["score"]
        print(
            f"  match {fixture.match_number}: {score['home']}-{score['away']} "
            f"Y={parsed['yellowCards']} directR={parsed['directRedCards']}"
        )
        synced += 1

    top_scorer_updated = sync_top_scorer_espn(store, now=now, dry_run=dry_run)
    if synced or top_scorer_updated:
        save_results(store)
        totals = store.get("tournamentTotals", {})
        if synced:
            print(f"Saved {synced} result(s). Totals: {totals}")

    return synced


def _sync_results_api_football(*, dry_run: bool = False, force_remap: bool = False) -> int:
    now = datetime.now(timezone.utc)
    store = load_results()
    season = default_season()
    fixture_map = build_fixture_map(season=season, force=force_remap)
    pending_numbers = [
        fixture.match_number
        for fixture in _pending_fixtures(
            now,
            store,
            require_fixture_map=True,
            fixture_map=fixture_map,
        )
    ]

    if not fixture_map:
        print(f"No fixture map for season {season} (API plan may not include this season yet).")
        return 0

    if not pending_numbers:
        print("No newly finished matches to sync.")
        if sync_top_scorer_api_football(store, season=season, dry_run=dry_run):
            save_results(store)
        return 0

    fixture_ids = [fixture_map[match_number] for match_number in pending_numbers]
    print(f"Syncing {len(pending_numbers)} match(es): {pending_numbers}")
    if dry_run:
        print(f"Would call /fixtures?ids= in {(len(fixture_ids) + 19) // 20} batch(es)")
        return 0

    api_fixtures = fetch_fixtures_by_ids(fixture_ids)
    by_id = {
        int(fixture["fixture"]["id"]): fixture
        for fixture in api_fixtures
        if isinstance(fixture.get("fixture"), dict) and fixture["fixture"].get("id") is not None
    }

    synced = 0
    for match_number in pending_numbers:
        fixture_id = fixture_map[match_number]
        fixture = by_id.get(fixture_id)
        if fixture is None:
            print(f"  match {match_number}: fixture {fixture_id} not returned")
            continue

        parsed = parse_fixture_result(fixture)
        if parsed is None:
            status = fixture.get("fixture", {}).get("status", {}).get("short")
            print(f"  match {match_number}: not finished yet (status={status})")
            continue

        upsert_match_result(store, match_number, parsed)
        score = parsed["score"]
        print(
            f"  match {match_number}: {score['home']}-{score['away']} "
            f"Y={parsed['yellowCards']} directR={parsed['directRedCards']}"
        )
        synced += 1

    top_scorer_updated = sync_top_scorer_api_football(store, season=season, dry_run=dry_run)
    if synced or top_scorer_updated:
        save_results(store)
        totals = store.get("tournamentTotals", {})
        if synced:
            print(f"Saved {synced} result(s). Totals: {totals}")

    return synced
