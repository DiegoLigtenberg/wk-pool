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


def _iter_scored_matches(tournament: dict) -> list[dict]:
    matches: list[dict] = []
    for group in tournament.get("groups", []):
        if not isinstance(group, dict):
            continue
        for match in group.get("matches", []):
            if isinstance(match, dict):
                matches.append(match)
    for match in tournament.get("knockoutMatches", []):
        if isinstance(match, dict):
            matches.append(match)
    return matches


def build_store(tournament: dict) -> dict[str, object]:
    matches: dict[str, object] = {}
    for match in _iter_scored_matches(tournament):
        score = match.get("score")
        if not score or not isinstance(score, dict):
            continue
        entry: dict[str, object] = {
            "score": {"home": int(score["home"]), "away": int(score["away"])}
        }
        if match.get("advancingTeam") in {"home", "away"}:
            entry["advancingTeam"] = match["advancingTeam"]
        matches[str(match["matchNumber"])] = entry

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
