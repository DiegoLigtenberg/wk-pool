"""Toon hoe research-teksten in de UI landen (na humanize)."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.display_text import humanize_research_line, humanize_team_spark
from app.teams import display_team_name

ROOT = Path(__file__).resolve().parents[1] / "app" / "data" / "teams" / "research"


def main() -> int:
    print("=== distinctive_spark_notes (teamvisie) ===\n")
    for path in sorted(ROOT.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        spark = data.get("distinctive_spark_notes")
        if not spark:
            continue
        team = str(data.get("team_id") or path.stem)
        readable = humanize_team_spark(str(spark), team)
        if readable != normalize(str(spark)):
            print(f"[{team}]")
            print(f"  raw:  {spark!r:.120}")
            print(f"  UI:   {readable}")
            print()

    return 0


def normalize(s: str) -> str:
    return " ".join(s.split())


if __name__ == "__main__":
    raise SystemExit(main())
