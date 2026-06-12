"""POST to the backend internal sync endpoint (Railway cron only)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _running_on_railway() -> bool:
    return bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_SERVICE_NAME"))


def main(argv: list[str] | None = None) -> int:
    if not _running_on_railway():
        print(
            "This script only runs on Railway (wk-pool-cron-sync). "
            "Results sync automatically via cron — no local trigger needed.",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-remap", action="store_true", help="Ask backend to rebuild API-Football fixture map")
    args = parser.parse_args(argv)

    backend_url = os.environ.get("BACKEND_URL", "").rstrip("/")
    secret = os.environ.get("FOOTBALL_SYNC_SECRET", "").strip()

    if not backend_url:
        print("Missing BACKEND_URL on the cron service.", file=sys.stderr)
        return 1
    if not secret:
        print("Missing FOOTBALL_SYNC_SECRET on the cron service.", file=sys.stderr)
        return 1

    path = "/internal/sync-football"
    if args.force_remap:
        path += "?force-remap=1"

    request = urllib.request.Request(
        f"{backend_url}{path}",
        method="POST",
        headers={"Authorization": f"Bearer {secret}"},
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"Sync trigger failed ({error.code}): {detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"Sync trigger failed: {error.reason}", file=sys.stderr)
        return 1

    print(body)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return 0

    if payload.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
