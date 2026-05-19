"""Vind cryptische UI-teksten in team-YAML (matchup, spark, crowd, context_scoring)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "teams" / "research"
OUT = Path(__file__).resolve().parent / "audit_research_clarity.json"

UI_LIST_FIELDS = ("matchup_counters_us", "matchup_we_counter")
UI_TEXT_FIELDS = ("distinctive_spark_notes", "crowd_home_bias_notes")

# Geen werkwoord / alleen label
NO_VERB = re.compile(
    r"^(?!.*\b(is|zijn|heeft|hebben|moet|kan|wordt|leunt|zet|speelt|volgde|blijft|vraagt|helpt|maakt)\b).+$",
    re.I,
)

LAND_PLAYER = re.compile(r"^[A-Za-zÀ-ÿ\s\-']+\s+[A-Z][a-zà-ü\-']+(\s+[A-Z][a-zà-ü\-']+)?\.?$")
COLON_SHORT = re.compile(r"^[A-Za-zÀ-ÿ\s\-]+:\s*[^.]{2,25}\.?$")
JARGON_MARKERS = (
    "NY/LA",
    "diaspora",
    "Zwakwer",
    "erfgois",
    "heruitvind",
    "plot-twist",
    "arm-fit",
    "possession-model",
    "PPDA",
    "morpht",
    "woestijn",
    "t.o.v.",
    "co-host",
    "/Miami",
)


def score_line(text: str) -> tuple[int, list[str]]:
    t = text.strip()
    flags: list[str] = []
    score = 0
    words = len(t.split())

    if words <= 4:
        score += 3
        flags.append("≤4 woorden")
    elif words <= 7:
        score += 2
        flags.append("≤7 woorden")

    if LAND_PLAYER.match(t) and " " in t:
        score += 4
        flags.append("land+naam")

    if COLON_SHORT.match(t):
        score += 3
        flags.append("kort_met_dubbele_punt")

    if any(m in t for m in JARGON_MARKERS):
        score += 2
        flags.append("jargon")

    if NO_VERB.match(t) and words <= 10:
        score += 1
        flags.append("weinig_werkwoord")

    if re.search(r"\btest\.?$|\bvs\b", t, re.I) and words <= 5:
        score += 3
        flags.append("losse_notitie")

    return score, flags


def collect(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    team = data.get("team_id") or path.stem
    rows: list[dict] = []

    for field in UI_TEXT_FIELDS:
        val = data.get(field)
        if isinstance(val, str) and val.strip():
            sc, flags = score_line(val)
            if sc >= 3:
                rows.append({"team": team, "field": field, "text": val.strip(), "score": sc, "flags": flags})

    for field in UI_LIST_FIELDS:
        for i, line in enumerate(data.get(field) or []):
            if isinstance(line, str) and line.strip():
                sc, flags = score_line(line)
                if sc >= 3:
                    rows.append(
                        {
                            "team": team,
                            "field": f"{field}[{i}]",
                            "text": line.strip(),
                            "score": sc,
                            "flags": flags,
                        }
                    )

    scoring = data.get("context_scoring") or {}
    for i, f in enumerate(scoring.get("persistent") or []):
        if isinstance(f, dict) and f.get("reason"):
            sc, flags = score_line(str(f["reason"]))
            if sc >= 3:
                rows.append(
                    {
                        "team": team,
                        "field": f"context_scoring.persistent[{i}]",
                        "text": str(f["reason"]).strip(),
                        "score": sc,
                        "flags": flags,
                    }
                )
    for opp, flist in (scoring.get("versus") or {}).items():
        for i, f in enumerate(flist or []):
            if isinstance(f, dict) and f.get("reason"):
                sc, flags = score_line(str(f["reason"]))
                if sc >= 4:
                    rows.append(
                        {
                            "team": team,
                            "field": f"context_scoring.versus.{opp}[{i}]",
                            "text": str(f["reason"]).strip(),
                            "score": sc,
                            "flags": flags,
                        }
                    )

    return rows


def main() -> int:
    all_rows: list[dict] = []
    for path in sorted(RESEARCH_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        all_rows.extend(collect(path))

    all_rows.sort(key=lambda r: (-r["score"], r["team"]))
    OUT.write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(all_rows)} regels met score >= 3 (UI-velden)")
    print(f"Geschreven naar {OUT}")
    for row in all_rows[:25]:
        print(f"\n[{row['score']}] {row['team']} — {row['field']}")
        print(f"  {row['text'][:100]}")
        print(f"  ({', '.join(row['flags'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
