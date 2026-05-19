"""Schrijf `context_scoring` naar alle team-YAML (eenmalig / na research-update).

Run: cd src/backend && python -m app.data.teams.build_context_scoring_yaml
"""

from __future__ import annotations

import yaml

from app.data.teams.context_scoring_builder import build_context_scoring, context_scoring_to_yaml_dict
from app.data.teams.team_loader import TEAMS_DIR, _parse_bundle

RESEARCH_DIR = TEAMS_DIR / "research"


def main() -> int:
    bundles: dict[str, tuple] = {}
    for path in sorted(RESEARCH_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        bundle = _parse_bundle(path, data)
        bundles[bundle.fifa_team_key] = (path, data, bundle)

    by_fifa = {fifa: item[2] for fifa, item in bundles.items()}
    updated = 0
    for fifa, (path, data, bundle) in bundles.items():
        scoring = build_context_scoring(bundle, by_fifa)
        data["context_scoring"] = context_scoring_to_yaml_dict(scoring)
        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        updated += 1
    print(f"context_scoring geschreven voor {updated} teams")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
