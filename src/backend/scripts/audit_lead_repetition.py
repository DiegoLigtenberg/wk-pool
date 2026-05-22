"""Flag herhaalde zinnen in leadSummary over groepsduels (zelfde team)."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()

from app.data.teams.team_loader import load_all_bundles
from app.predictions import predict_match
from app.teams import display_team_name, fifa_team_key

OUT = Path(__file__).resolve().parent / "audit_lead_repetition.json"

_MIN_SENTENCE_LEN = 42

# Bekende teamverhalen: zelfde fragment in 2+ groepsduels is te veel.
_FRAGMENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("james_rodriguez", re.compile(r"james rodr[ií]guez", re.I)),
    ("ancelotti", re.compile(r"ancelotti", re.I)),
    ("modric", re.compile(r"modri[cć].*nog steeds geselecteerd", re.I)),
)


def _duels_by_team() -> dict[str, list[tuple[str, str]]]:
    bundles = load_all_bundles()
    by_team: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for fifa, bundle in bundles.items():
        for opp_fifa in bundle.group_stage.opponents_fifa:
            opp_key = fifa_team_key(opp_fifa)
            if opp_key not in bundles:
                continue
            pred = predict_match(fifa, opp_key, "group", "1", None)
            lead = str(pred.get("insight", {}).get("leadSummary") or "")
            label = f"{bundle.team_name_nl} – {display_team_name(opp_fifa)}"
            by_team[bundle.team_name_nl].append((label, lead))
    return by_team


def _sentences(lead: str) -> list[str]:
    return [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", lead)
        if len(s.strip()) >= _MIN_SENTENCE_LEN
    ]


def collect_hits() -> list[dict]:
    hits: list[dict] = []
    for team, duels in sorted(_duels_by_team().items()):
        for frag_id, pattern in _FRAGMENT_PATTERNS:
            matches = [label for label, lead in duels if pattern.search(lead)]
            if len(matches) >= 2:
                hits.append(
                    {
                        "kind": "fragment",
                        "team": team,
                        "fragment": frag_id,
                        "count": len(matches),
                        "matches": matches,
                    }
                )

        sentence_map: dict[str, list[str]] = defaultdict(list)
        for label, lead in duels:
            for sentence in _sentences(lead):
                key = re.sub(r"\s+", " ", sentence.lower())
                sentence_map[key].append(label)

        for sentence, labels in sentence_map.items():
            if len(labels) >= 2:
                hits.append(
                    {
                        "kind": "duplicate_sentence",
                        "team": team,
                        "count": len(labels),
                        "matches": labels,
                        "sentence": sentence[:100],
                    }
                )
    return hits


def main() -> int:
    hits = collect_hits()
    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Herhalings-issues: {len(hits)}")
    print(f"JSON: {OUT}\n")
    for row in hits[:25]:
        kind = row["kind"]
        if kind == "fragment":
            print(
                f"  [{row['fragment']}] {row['team']}: {row['count']}× "
                f"({', '.join(row['matches'][:3])})"
            )
        else:
            print(
                f"  [zelfde zin] {row['team']}: {row['count']}×, {row['sentence'][:80]}…"
            )
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
