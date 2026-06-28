"""Bootstrap local match-results.json from production tournament API (dev only)."""

from __future__ import annotations

import argparse
import json
import urllib.request

from app.match_results_store import save_results

DEFAULT_URL = "https://wk-pool-backend.up.railway.app/api/tournament"


def _fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)


def build_store(tournament: dict) -> dict[str, object]:
    matches: dict[str, object] = {}
    for group in tournament.get("groups", []):
        if not isinstance(group, dict):
            continue
        for match in group.get("matches", []):
            if not isinstance(match, dict):
                continue
            score = match.get("score")
            if not score or not isinstance(score, dict):
                continue
            matches[str(match["matchNumber"])] = {
                "score": {"home": int(score["home"]), "away": int(score["away"])}
            }

    return {
        "version": 1,
        "updatedAt": tournament.get("resultsUpdatedAt"),
        "matches": matches,
        "tournamentTotals": tournament.get(
            "cardTotals", {"yellowCards": 0, "directRedCards": 0}
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="Production tournament API URL")
    args = parser.parse_args(argv)

    tournament = _fetch(args.url)
    store = build_store(tournament)
    save_results(store)
    print(f"Wrote {len(store['matches'])} results. Herstart de backend (cache).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
