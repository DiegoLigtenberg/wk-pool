"""Sync finished match scores and cards from API-Football into match-results.json."""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.football_api import (
    fetch_fixtures_by_ids,
    fetch_league_fixtures,
    match_api_fixture,
    parse_fixture_result,
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
from app.tournament import load_fixtures


def _season() -> int:
    return int(os.environ.get("FOOTBALL_API_SEASON", "2026"))


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


def _candidates(now: datetime, fixture_map: dict[int, int], store: dict[str, object]) -> list[int]:
    pending: list[int] = []
    for fixture in load_fixtures():
        if fixture.match_number not in fixture_map:
            continue
        if now < _ready_at(fixture.kickoff_at):
            continue
        if result_for_match(store, fixture.match_number) is not None:
            continue
        pending.append(fixture.match_number)
    return pending


def sync_results(*, dry_run: bool = False, force_remap: bool = False) -> int:
    now = datetime.now(timezone.utc)
    store = load_results()
    fixture_map = build_fixture_map(season=_season(), force=force_remap)
    candidates = _candidates(now, fixture_map, store)

    if not fixture_map:
        print(f"No fixture map for season {_season()} (API plan may not include this season yet).")
        return 0

    if not candidates:
        print("No newly finished matches to sync.")
        return 0

    fixture_ids = [fixture_map[match_number] for match_number in candidates]
    print(f"Syncing {len(candidates)} match(es): {candidates}")
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
    for match_number in candidates:
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

    if synced:
        save_results(store)
        totals = store.get("tournamentTotals", {})
        print(f"Saved {synced} result(s). Totals: {totals}")

    return synced


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would sync without API writes")
    parser.add_argument("--force-remap", action="store_true", help="Rebuild CSV → API fixture id map")
    parser.add_argument("--season", type=int, default=_season(), help="API season year (default: FOOTBALL_API_SEASON or 2026)")
    args = parser.parse_args()

    os.environ["FOOTBALL_API_SEASON"] = str(args.season)

    try:
        sync_results(dry_run=args.dry_run, force_remap=args.force_remap)
    except Exception as error:  # noqa: BLE001 - CLI entrypoint
        print(f"Sync failed: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
