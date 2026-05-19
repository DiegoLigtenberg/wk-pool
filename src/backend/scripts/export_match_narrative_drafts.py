"""Export per wedstrijd de feiten + template-tekst voor handmatige of LLM-polish (geen runtime-LLM).

Run:
  cd src/backend
  poetry run python scripts/export_match_narrative_drafts.py

Output: app/data/narratives/drafts.md (gitignored optioneel)
"""

from __future__ import annotations

import json
from pathlib import Path

from app.tournament import load_fixtures
from app.predictions import predict_match
OUT = Path(__file__).resolve().parents[1] / "app" / "data" / "narratives" / "drafts.md"


def main() -> int:
    fixtures = [f for f in load_fixtures() if f.group is not None][:12]
    lines = [
        "# Wedstrijd-narratieven (draft)",
        "",
        "Gebruik dit bestand om teksten te polijsten. De app gebruikt standaard de",
        "template-generator in `prediction_narrative.py` (geen API bij runtime).",
        "",
        "Workflow met LLM (optioneel, offline):",
        "1. Run dit script.",
        "2. Laat een LLM per wedstrijd `narrative` herschrijven in vloeiend Nederlands.",
        "3. Sla op als `overrides/{home}_vs_{away}.json` met velden `narrative`, `steps`.",
        "",
        "---",
        "",
    ]

    for fx in fixtures:
        pred = predict_match(fx.home_team, fx.away_team, "group", fx.round_number, fx.group)
        insight = pred["insight"]
        lines.append(f"## {fx.home_team} - {fx.away_team} (groep {fx.group}, ronde {fx.round_number})")
        lines.append("")
        lines.append(f"**Pick:** {pred['pick']} ({pred['confidence']}%)")
        lines.append("")
        lines.append("### Automatische narrative")
        lines.append("")
        lines.append(str(insight["narrative"]))
        lines.append("")
        lines.append("### Stappen")
        lines.append("")
        for step in insight["steps"]:
            lines.append(f"**{step['title']}**")
            lines.append("")
            lines.append(step["body"])
            lines.append("")
        lines.append("<details><summary>Raw JSON</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(insight, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append("---")
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Geschreven: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
