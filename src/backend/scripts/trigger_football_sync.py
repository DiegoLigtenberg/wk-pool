"""POST to the backend internal sync endpoint (Railway cron only)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

RETRYABLE_HTTP_CODES = frozenset({502, 503, 504})
MAX_ATTEMPTS = 4
RETRY_DELAY_SECONDS = 5


def _running_on_railway() -> bool:
    return bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_SERVICE_NAME"))


def _warn_if_frontend_url(backend_url: str) -> None:
    if backend_url.endswith("wk-pool.up.railway.app"):
        print(
            "Warning: BACKEND_URL looks like the frontend. Use the backend service URL, "
            "e.g. https://wk-pool-backend.up.railway.app",
            file=sys.stderr,
        )


def _request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, timeout: int = 30) -> str:
    request = urllib.request.Request(url, method=method, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _warm_backend(backend_url: str) -> None:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            _request(f"{backend_url}/health", timeout=30)
            return
        except urllib.error.HTTPError as error:
            if error.code not in RETRYABLE_HTTP_CODES or attempt == MAX_ATTEMPTS:
                raise
        except urllib.error.URLError:
            if attempt == MAX_ATTEMPTS:
                raise
        print(f"Backend warm-up attempt {attempt}/{MAX_ATTEMPTS} failed; retrying...", file=sys.stderr)
        time.sleep(RETRY_DELAY_SECONDS)


def _trigger_sync(backend_url: str, secret: str, *, force_remap: bool) -> str:
    path = "/internal/sync-football"
    if force_remap:
        path += "?force-remap=1"

    headers = {"Authorization": f"Bearer {secret}"}
    url = f"{backend_url}{path}"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return _request(url, method="POST", headers=headers, timeout=120)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code not in RETRYABLE_HTTP_CODES or attempt == MAX_ATTEMPTS:
                print(f"Sync trigger failed ({error.code}): {detail}", file=sys.stderr)
                raise
            print(
                f"Sync trigger attempt {attempt}/{MAX_ATTEMPTS} got {error.code}; retrying...",
                file=sys.stderr,
            )
        except urllib.error.URLError as error:
            if attempt == MAX_ATTEMPTS:
                print(f"Sync trigger failed: {error.reason}", file=sys.stderr)
                raise
            print(
                f"Sync trigger attempt {attempt}/{MAX_ATTEMPTS} failed ({error.reason}); retrying...",
                file=sys.stderr,
            )
        time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError("unreachable")


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

    _warn_if_frontend_url(backend_url)

    try:
        _warm_backend(backend_url)
        body = _trigger_sync(backend_url, secret, force_remap=args.force_remap)
    except (urllib.error.HTTPError, urllib.error.URLError):
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
