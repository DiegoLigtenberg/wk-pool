"""POST to the backend internal sync endpoint (for Railway cron without a shared volume)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from app.football_api import load_env_file

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def read_dotenv_value(key: str) -> str | None:
    if not ENV_PATH.exists():
        return None

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
            continue
        env_key, value = clean_line.split("=", 1)
        if env_key.strip() != key:
            continue
        cleaned = value.strip().strip('"').strip("'")
        return cleaned or None

    return None


def resolve_secret(cli_secret: str | None) -> str:
    if cli_secret:
        return cli_secret.strip()
    dotenv_secret = read_dotenv_value("FOOTBALL_SYNC_SECRET")
    if dotenv_secret:
        return dotenv_secret
    return os.environ.get("FOOTBALL_SYNC_SECRET", "").strip()


def resolve_backend_url(cli_backend_url: str | None) -> str:
    if cli_backend_url:
        return cli_backend_url.rstrip("/")
    dotenv_url = read_dotenv_value("BACKEND_URL")
    if dotenv_url:
        return dotenv_url.rstrip("/")
    return os.environ.get("BACKEND_URL", "").rstrip("/")


def main(argv: list[str] | None = None) -> int:
    load_env_file()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend-url",
        default=None,
        help="Backend base URL (default: BACKEND_URL in .env, else env var)",
    )
    parser.add_argument(
        "--secret",
        default=None,
        help="Bearer token (default: FOOTBALL_SYNC_SECRET in .env, else env var)",
    )
    parser.add_argument("--force-remap", action="store_true", help="Ask backend to rebuild fixture map")
    args = parser.parse_args(argv)

    backend_url = resolve_backend_url(args.backend_url)
    secret = resolve_secret(args.secret)

    if not backend_url:
        print("Missing backend URL. Set BACKEND_URL in .env, env var, or pass --backend-url.", file=sys.stderr)
        return 1
    if not secret:
        print("Missing sync secret. Set FOOTBALL_SYNC_SECRET in .env, env var, or pass --secret.", file=sys.stderr)
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
        if error.code == 401:
            print(
                "401 = verkeerde FOOTBALL_SYNC_SECRET. Moet exact gelijk zijn aan Railway backend "
                "(Variables). Oude $env:FOOTBALL_SYNC_SECRET in PowerShell? Sluit terminal of: "
                "Remove-Item Env:FOOTBALL_SYNC_SECRET",
                file=sys.stderr,
            )
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
