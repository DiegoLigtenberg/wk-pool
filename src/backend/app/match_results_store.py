"""Persist synced match results from API-Football."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

_DATA_DIR = Path(os.environ.get("WK_POOL_DATA_DIR", "")).expanduser() if os.environ.get("WK_POOL_DATA_DIR") else None
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
RESULTS_PATH = (_DATA_DIR or _DEFAULT_DATA_DIR) / "match-results.json"
FIXTURE_MAP_PATH = (_DATA_DIR or _DEFAULT_DATA_DIR) / "football-fixture-map.json"


def _empty_store() -> dict[str, object]:
    return {
        "version": 1,
        "updatedAt": None,
        "matches": {},
        "tournamentTotals": {"yellowCards": 0, "directRedCards": 0},
    }


def load_results(path: Path = RESULTS_PATH) -> dict[str, object]:
    if not path.exists():
        return _empty_store()

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return _empty_store()
    data.setdefault("matches", {})
    data.setdefault("tournamentTotals", {"yellowCards": 0, "directRedCards": 0})
    return data


def save_results(store: dict[str, object], path: Path = RESULTS_PATH) -> None:
    store["updatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_fixture_map(path: Path = FIXTURE_MAP_PATH) -> dict[str, int]:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    matches = data.get("matches", {})
    if not isinstance(matches, dict):
        return {}

    return {str(key): int(value) for key, value in matches.items()}


def save_fixture_map(mapping: dict[int, int], path: Path = FIXTURE_MAP_PATH) -> None:
    payload = {
        "version": 1,
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "matches": {str(match_number): fixture_id for match_number, fixture_id in sorted(mapping.items())},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def result_for_match(store: dict[str, object], match_number: int) -> dict[str, object] | None:
    matches = store.get("matches")
    if not isinstance(matches, dict):
        return None
    entry = matches.get(str(match_number))
    return entry if isinstance(entry, dict) else None


def recompute_totals(store: dict[str, object]) -> None:
    matches = store.get("matches")
    if not isinstance(matches, dict):
        return

    yellow_total = 0
    red_total = 0
    for entry in matches.values():
        if not isinstance(entry, dict):
            continue
        yellow_total += int(entry.get("yellowCards", 0))
        red_total += int(entry.get("directRedCards", 0))

    store["tournamentTotals"] = {
        "yellowCards": yellow_total,
        "directRedCards": red_total,
    }


def upsert_match_result(
    store: dict[str, object],
    match_number: int,
    result: dict[str, object],
) -> None:
    matches = store.setdefault("matches", {})
    if not isinstance(matches, dict):
        raise TypeError("matches must be a mapping")

    matches[str(match_number)] = result
    recompute_totals(store)
