"""Sync finished match scores and cards from API-Football into match-results.json."""

from __future__ import annotations

import argparse
import os
import sys

from app.football_sync import default_season, sync_results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would sync without API writes")
    parser.add_argument("--force-remap", action="store_true", help="Rebuild CSV → API fixture id map")
    parser.add_argument(
        "--season",
        type=int,
        default=default_season(),
        help="API season year (default: FOOTBALL_API_SEASON or 2026)",
    )
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
