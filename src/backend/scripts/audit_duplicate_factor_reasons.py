"""Zoek dubbele factorregels met (bijna) dezelfde tekst in AI-insight UI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()

from app.data.teams.team_loader import load_all_bundles
from app.predictions import predict_match
from app.teams import display_team_name, fifa_team_key

OUT = Path(__file__).resolve().parent / "audit_duplicate_factor_reasons.json"


def _normalize_reason(text: str) -> str:
    return " ".join(text.lower().split())[:120]


def main() -> int:
    bundles = load_all_bundles()
    hits: list[dict] = []
    for fifa, bundle in bundles.items():
        for opp in bundle.group_stage.opponents_fifa:
            opp_key = fifa_team_key(opp)
            if opp_key not in bundles:
                continue
            pred = predict_match(fifa, opp_key, "group", "1", None)
            for side_key in ("home", "away"):
                side = pred["insight"][side_key]
                factors = [f for f in side["factors"] if f.get("delta")]
                by_reason: dict[str, list[dict]] = {}
                for factor in factors:
                    reason = _normalize_reason(str(factor.get("reason", "")))
                    if len(reason) < 24:
                        continue
                    by_reason.setdefault(reason, []).append(factor)
                for reason, group in by_reason.items():
                    if len(group) < 2:
                        continue
                    ids = [str(f["id"]) for f in group]
                    if len(set(ids)) < 2:
                        continue
                    hits.append(
                        {
                            "match": f"{display_team_name(fifa)} – {display_team_name(opp)}",
                            "team": side["team"],
                            "reason": reason,
                            "factors": [
                                {
                                    "id": f["id"],
                                    "delta": f["delta"],
                                    "scope": f.get("scope"),
                                }
                                for f in group
                            ],
                        }
                    )

    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Dubbele factor-teksten in insight UI: {len(hits)}")
    print(f"JSON: {OUT}\n")
    for row in hits[:20]:
        print(row["match"], "—", row["team"])
        for f in row["factors"]:
            print(f"  {f['id']} {f['delta']:+d} ({f.get('scope')})")
        print(f"  → {row['reason'][:100]}…\n")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
