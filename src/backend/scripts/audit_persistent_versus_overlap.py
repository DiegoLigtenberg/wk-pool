"""Audit: dubbele telling persistent + versus in opgeslagen context_scoring."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()

import re
from collections import defaultdict

from app.data.teams.context_score import match_context_breakdown, side_context
from app.data.teams.factor_dedupe import dedupe_overlapping_factors
from app.data.teams.team_loader import load_all_bundles
from app.teams import fifa_team_key

INJURY_HINTS = ("out", "afwezig", "knie", "blessure", "geschorst", "uitgeschakeld")
STOP = frozenset(
    {
        "nederland",
        "oranje",
        "speelt",
        "wedstrijd",
        "zonder",
        "definitief",
        "creatie",
        "structureel",
        "verzwakt",
        "kwetsbaar",
        "structureel",
    }
)


def _tokens(s: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z\u00c0-\u024f]{4,}", s.lower())
        if t not in STOP
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main() -> None:
    bundles = load_all_bundles()
    issues: dict[str, list[str]] = defaultdict(list)

    for fifa, bundle in bundles.items():
        scoring = bundle.context_scoring
        if scoring is None:
            continue

        for opp_fifa, versus_factors in scoring.versus.items():
            ids = [f.id for f in versus_factors]
            dups = {i for i in ids if ids.count(i) > 1}
            if dups:
                issues["yaml_duplicate_factor_id"].append(
                    f"{bundle.team_name_nl} vs {opp_fifa}: {sorted(dups)}"
                )

        for pers in scoring.persistent:
            pl = pers.reason.lower()
            for opp_fifa, versus_factors in scoring.versus.items():
                for vf in versus_factors:
                    ja = _jaccard(_tokens(pers.reason), _tokens(vf.reason))
                    if ja >= 0.35:
                        issues["yaml_similar_text"].append(
                            f"{bundle.team_name_nl} vs {opp_fifa}: "
                            f"{pers.id}({pers.delta}) + {vf.id}({vf.delta}) "
                            f"j={ja:.2f}"
                        )
                    if any(h in pl for h in INJURY_HINTS) and any(
                        h in vf.reason.lower() for h in INJURY_HINTS
                    ):
                        shared = _tokens(pl) & _tokens(vf.reason.lower())
                        if len(shared) >= 2:
                            issues["injury_in_both_layers"].append(
                                f"{bundle.team_name_nl} vs {opp_fifa}: "
                                f"{pers.id} + {vf.id} shared={sorted(shared)[:6]}"
                            )

        for opp in bundle.group_stage.opponents_fifa:
            opp_key = fifa_team_key(opp)
            raw = list(scoring.persistent) + list(scoring.versus.get(opp_key, ()))
            deduped = dedupe_overlapping_factors(raw)
            if sum(f.delta for f in raw) != sum(f.delta for f in deduped):
                issues["runtime_dedupe_changes_delta"].append(
                    f"{bundle.team_name_nl} vs {opp_key}: "
                    f"{sum(f.delta for f in raw)} -> {sum(f.delta for f in deduped)}"
                )

    for host in ("USA", "Mexico", "Canada"):
        if host not in bundles:
            continue
        bundle = bundles[host]
        for opp in bundle.group_stage.opponents_fifa:
            ctx = side_context(host, opp)
            if ctx.host_delta and any(f.id == "cohost_crowd" for f in ctx.factors):
                issues["cohost_group_plus_host"].append(
                    f"{bundle.team_name_nl} vs {opp}: "
                    f"research {ctx.research_delta} incl. cohost_crowd + host +{ctx.host_delta}"
                )

    seen_pairs: set[tuple[str, str]] = set()
    for fifa, bundle in bundles.items():
        for opp in bundle.group_stage.opponents_fifa:
            opp_key = fifa_team_key(opp)
            if opp_key not in bundles:
                continue
            pair = tuple(sorted((fifa, opp_key)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            br = match_context_breakdown(fifa, opp_key)
            for side_key in ("home", "away"):
                side = br[side_key]
                plus_styles = [
                    r
                    for r in side["reasons"]
                    if r["id"] == "style_matchup" and r["delta"] > 0
                ]
                if len(plus_styles) > 1:
                    issues["score_multiple_plus_style"].append(
                        f"{side['team']}: {len(plus_styles)}x +1 style_matchup"
                    )

    print("=== Persistent vs versus overlap audit ===\n")
    for key in sorted(issues):
        items = issues[key]
        print(f"{key}: {len(items)}")
        for item in items[:12]:
            print(f"  - {item}")
        if len(items) > 12:
            print(f"  ... +{len(items) - 12} more")
        print()


if __name__ == "__main__":
    main()
