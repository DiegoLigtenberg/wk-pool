"""POST to the backend internal sync endpoint (for Railway cron without a shared volume)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend-url",
        default=os.environ.get("BACKEND_URL", "").rstrip("/"),
        help="Backend base URL (default: BACKEND_URL env var)",
    )
    parser.add_argument(
        "--secret",
        default=os.environ.get("FOOTBALL_SYNC_SECRET", ""),
        help="Bearer token (default: FOOTBALL_SYNC_SECRET env var)",
    )
    parser.add_argument("--force-remap", action="store_true", help="Ask backend to rebuild fixture map")
    args = parser.parse_args(argv)

    if not args.backend_url:
        print("Missing backend URL. Set BACKEND_URL or pass --backend-url.", file=sys.stderr)
        return 1
    if not args.secret:
        print("Missing sync secret. Set FOOTBALL_SYNC_SECRET or pass --secret.", file=sys.stderr)
        return 1

    path = "/internal/sync-football"
    if args.force_remap:
        path += "?force-remap=1"

    request = urllib.request.Request(
        f"{args.backend_url}{path}",
        method="POST",
        headers={"Authorization": f"Bearer {args.secret}"},
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
