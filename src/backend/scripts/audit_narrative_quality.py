"""Valideer research-redenen en AI-voorspellingsteksten op afkappingen en cryptische notities."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()

import json
import re
from pathlib import Path

import yaml

from app.data.teams.team_loader import load_all_bundles
from app.display_text import looks_truncated_reason
from app.predictions import predict_match
from app.teams import display_team_name, fifa_team_key

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "teams" / "research"
OUT = Path(__file__).resolve().parent / "audit_narrative_quality.json"

CRYPTIC = re.compile(
    r"^(?:[A-Za-zÀ-ÿ\-]+(?:/[A-Za-zÀ-ÿ\-]+)*\s*){1,3}\.?$|"
    r"^[A-Za-zÀ-ÿ\-]+:\s*[A-Za-z].{0,30}\.?$",
)
SHORT_WORDS = 5


def _yield_reasons(scoring: dict) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for i, factor in enumerate(scoring.get("persistent") or []):
        if isinstance(factor, dict) and factor.get("reason"):
            rows.append((f"persistent[{i}]", str(factor["reason"])))
    for opp, flist in (scoring.get("versus") or {}).items():
        for i, factor in enumerate(flist or []):
            if isinstance(factor, dict) and factor.get("reason"):
                rows.append((f"versus.{opp}[{i}]", str(factor["reason"])))
    return rows


def audit_yaml() -> list[dict]:
    hits: list[dict] = []
    for path in sorted(RESEARCH_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        team = str(data.get("team_id") or path.stem)
        spark = (data.get("distinctive_spark_notes") or "").replace("\n", " ").strip()
        for field, reason in _yield_reasons(data.get("context_scoring") or {}):
            text = reason.strip()
            flags: list[str] = []
            if looks_truncated_reason(text):
                flags.append("truncated")
            if len(text.split()) <= SHORT_WORDS and CRYPTIC.match(text):
                flags.append("cryptic_short")
            if spark and text in spark and len(text) < len(spark) - 12:
                flags.append("shorter_than_spark_notes")
            if flags:
                hits.append(
                    {
                        "kind": "yaml_reason",
                        "team": team,
                        "field": f"context_scoring.{field}",
                        "text": text,
                        "flags": flags,
                    }
                )
    return hits


def audit_predictions() -> list[dict]:
    hits: list[dict] = []
    bundles = load_all_bundles()
    for fifa, bundle in sorted(bundles.items(), key=lambda x: x[1].team_name_nl):
        for opp_fifa in bundle.group_stage.opponents_fifa:
            opp_key = fifa_team_key(opp_fifa)
            if opp_key not in bundles:
                continue
            pred = predict_match(fifa, opp_key, "group", "1", None)
            insight = pred.get("insight", {}) or {}
            why = str(
                insight.get("leadSummary")
                or (insight.get("steps", [{}, {}])[1].get("body") if insight.get("steps") else "")
            )
            flags: list[str] = []
            for sentence in re.split(r"(?<=[.!?])\s+", why):
                if sentence.strip() and looks_truncated_reason(sentence):
                    flags.append("truncated")
                    break
            if len(why) < 40:
                flags.append("very_short")
            if flags:
                hits.append(
                    {
                        "kind": "prediction_why",
                        "match": f"{bundle.team_name_nl} vs {display_team_name(opp_fifa)}",
                        "pick": pred.get("pick"),
                        "text": why,
                        "flags": flags,
                    }
                )
    return hits


def main() -> int:
    yaml_hits = audit_yaml()
    pred_hits = audit_predictions()
    all_hits = yaml_hits + pred_hits
    OUT.write_text(json.dumps(all_hits, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"YAML-redenen met problemen: {len(yaml_hits)}")
    print(f"Voorspellingsteksten met problemen: {len(pred_hits)}")
    print(f"Geschreven naar {OUT}\n")

    for row in all_hits[:30]:
        print(f"[{','.join(row['flags'])}] {row.get('team') or row.get('match')}, {row.get('field', 'why')}")
        print(f"  {row['text'][:140]}")
        print()

    return 1 if all_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
