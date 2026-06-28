"""One-off: download FIFA Annex C and write fifa_annex_c_third_place.json."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "app" / "data" / "fifa_annex_c_third_place.json"
URL = "https://raw.githubusercontent.com/manganite/wm2026/main/thirdPlaceAssignments.mjs"


def main() -> None:
    text = urllib.request.urlopen(URL, timeout=30).read().decode()
    rows = re.findall(r'"([A-Z]{8})"', text)
    winners_match = re.search(r'ANNEX_C_WINNERS = \[([^\]]+)\]', text)
    if not winners_match:
        raise RuntimeError("ANNEX_C_WINNERS not found")
    winners = [w.strip().strip('"') for w in winners_match.group(1).split(",")]

    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        groups = set(row)
        if len(groups) != 8:
            continue
        key = "".join(sorted(groups))
        lookup[key] = {winners[i]: row[i] for i in range(8)}

    OUT.write_text(
        json.dumps({"winners": winners, "lookup": lookup}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(lookup)} combinations to {OUT}")


if __name__ == "__main__":
    main()
