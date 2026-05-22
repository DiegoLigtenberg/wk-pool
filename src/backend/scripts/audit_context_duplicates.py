"""Zoek dubbele of spiegelende context-factoren in groepsduels."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()

from collections import defaultdict

from app.data.teams.context_scoring_builder import build_versus_factors
from app.data.teams.context_score import match_context_breakdown
from app.data.teams.pairwise_matchup import _is_self_weakness_note, _mentions_opponent
from app.data.teams.team_loader import load_all_bundles
from app.teams import fifa_team_key

bundles = load_all_bundles()
issues: dict[str, list] = defaultdict(list)


def raw_versus(team_fifa: str, opp_fifa: str):
    b = bundles[team_fifa]
    opp = bundles[fifa_team_key(opp_fifa)]
    return list(build_versus_factors(b, opp_fifa, opponent=opp))


for fifa, b in bundles.items():
    for opp_fifa in b.group_stage.opponents_fifa:
        opp_key = fifa_team_key(opp_fifa)
        if opp_key not in bundles:
            continue
        opp = bundles[opp_key]
        raw = raw_versus(fifa, opp_fifa)
        ids = [f.id for f in raw]

        if any(
            f.id == "opponent_profile_weak"
            for f in raw
            if _is_self_weakness_note(opp.phase_preferences[1])
        ):
            issues["zwakwer_opponent_profile_weak"].append(f"{b.team_name_nl} vs {opp.team_name_nl}")

        dup_ids = {i for i in ids if ids.count(i) > 1}
        if dup_ids:
            issues["duplicate_factor_id"].append(
                (
                    f"{b.team_name_nl} vs {opp.team_name_nl}",
                    dup_ids,
                    [f"{f.id}: {f.reason[:60]}" for f in raw if f.id in dup_ids],
                )
            )

        if any(f.id == "tactical_weakness" for f in raw) and any(
            f.id == "matchup_risk" for f in raw
        ):
            issues["weakness_and_matchup_risk"].append(f"{b.team_name_nl} vs {opp.team_name_nl}")

        opp_strong = opp.phase_preferences[0]
        if _mentions_opponent(opp_strong, b.team_name_nl, b.fifa_team_key):
            opp_raw = raw_versus(opp_key, fifa)
            if any(f.id == "opponent_profile_strong" for f in raw) and any(
                f.id == "tactical_strength" for f in opp_raw
            ):
                issues["sterk_mirror"].append(f"{b.team_name_nl} vs {opp.team_name_nl}")

for fifa, b in bundles.items():
    for opp_fifa in b.group_stage.opponents_fifa:
        opp_key = fifa_team_key(opp_fifa)
        if opp_key not in bundles or fifa >= opp_key:
            continue
        opp = bundles[opp_key]
        if any(f.id == "tactical_weakness" for f in raw_versus(fifa, opp_fifa)) and any(
            f.id == "tactical_weakness" for f in raw_versus(opp_key, fifa)
        ):
            issues["both_tactical_weakness"].append(f"{b.team_name_nl} vs {opp.team_name_nl}")

        br = match_context_breakdown(fifa, opp_fifa)
        home, away = br["home"], br["away"]
        for side in (home, away):
            plus_styles = [
                r for r in side["reasons"] if r["id"] == "style_matchup" and r["delta"] > 0
            ]
            if len(plus_styles) > 1:
                issues["runtime_dup_style"].append(
                    (side["team"], [r["reason"][:70] for r in plus_styles])
                )
        h_plus = [
            r
            for r in home["reasons"]
            if r["id"] == "style_matchup" and r["delta"] > 0
        ]
        a_plus = [
            r
            for r in away["reasons"]
            if r["id"] == "style_matchup" and r["delta"] > 0
        ]
        if h_plus and a_plus:
            issues["both_teams_plus_style"].append(f"{home['team']} vs {away['team']}")

# Co-host dubbel in één wedstrijd (persistent + host)
for fifa in ("USA", "Mexico", "Canada"):
    if fifa not in bundles:
        continue
    b = bundles[fifa]
    for opp_fifa in b.group_stage.opponents_fifa:
        br = match_context_breakdown(fifa, opp_fifa)
        side = br["home"] if br["home"]["team"] == b.team_name_nl else br["away"]
        if side["hostDelta"] and any(
            r["id"] == "cohost_crowd" for r in side["reasons"]
        ):
            issues["cohost_persistent_and_match"].append(
                f"{side['team']} thuis vs {opp_fifa}: +1 groep + {side['hostDelta']} thuis"
            )

print("=== Context duplicate audit ===\n")
for key in sorted(issues):
    items = issues[key]
    print(f"{key}: {len(items)}")
    for item in items[:10]:
        print(f"  - {item}")
    if len(items) > 10:
        print(f"  ... +{len(items) - 10} more")
    print()
