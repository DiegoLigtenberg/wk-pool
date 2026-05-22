"""Audit: pick ↔ wedstrijdscore ↔ kansen ↔ zichtbare tekst (alle groepsduels)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.data.teams.context_score import match_context_breakdown
from app.data.teams.team_loader import load_all_bundles
from app.pool_edge import apply_adjustments, collect_pick_adjustments
from app.predictions import (
    GROUP_DRAW_ABS_DIFF_MAX,
    GROUP_DRAW_BASE_CLEAR_GAP,
    GROUP_DRAW_DIFF_CLEAR_MIN,
    _clear_favorite_overrides_draw,
    _pick_from_diff,
    predict_match,
)
from app.tournament import load_fixtures
from app.teams import display_team_name, fifa_team_key

OUT = Path(__file__).resolve().parent / "audit_pick_truth.json"

SCORE_IN_LEAD = re.compile(r"wedstrijdscore|\d+\s+punten", re.I)
WIN_IN_LEAD = re.compile(r"\bwint\b", re.I)


def _pick_label(p: str) -> str:
    return {"1": "thuis", "2": "uit", "3": "gelijk"}[p]


def _verdict_team(pick: str, home_nl: str, away_nl: str) -> str | None:
    v = {"1": home_nl, "2": away_nl, "3": None}[pick]
    return v


def _lead_implies_other_winner(lead: str, pick: str, home_nl: str, away_nl: str) -> bool:
    low = lead.lower()
    if pick == "1" and f"{away_nl.lower()} wint" in low:
        return True
    if pick == "2" and f"{home_nl.lower()} wint" in low:
        return True
    if pick == "3" and WIN_IN_LEAD.search(lead):
        return True
    return False


def _note_covers_pick(pick: str, note: str, *, diff: int, home_power: int, away_power: int) -> bool:
    if not note.strip():
        return False
    low = note.lower()
    if pick == "3":
        return "gelijk" in low
    if (
        pick in ("1", "2")
        and abs(diff) <= GROUP_DRAW_ABS_DIFF_MAX
        and _clear_favorite_overrides_draw(
            diff, home_power=home_power, away_power=away_power
        )
    ):
        return any(w in low for w in ("sterk", "favoriet", "papier", "sterkere"))
    if pick in ("1", "2"):
        return any(
            w in low for w in ("wint", "voordeel", "verwacht", "kansen", "sterk", "krap", "favoriet")
        )
    return True


def main() -> int:
    bundles = load_all_bundles()
    rows: list[dict[str, object]] = []
    issues: list[str] = []

    for fx in load_fixtures():
        if not fx.group:
            continue
        home_key = fifa_team_key(fx.home_team)
        away_key = fifa_team_key(fx.away_team)
        home_nl = display_team_name(home_key)
        away_nl = display_team_name(away_key)

        pred = predict_match(
            fx.home_team, fx.away_team, "group", "1", fx.group, match_number=fx.match_number
        )
        br = match_context_breakdown(home_key, away_key)
        base_diff = int(br["diff"])
        hp, ap = int(br["home"]["powerScore"]), int(br["away"]["powerScore"])
        pick = str(pred["pick"])
        probs = {
            "home": int(pred["homeWinProbability"] or 0),
            "draw": int(pred["drawProbability"] or 0),
            "away": int(pred["awayWinProbability"] or 0),
        }
        adj = collect_pick_adjustments(
            home_key=home_key,
            away_key=away_key,
            home_power=hp,
            away_power=ap,
            home_factors=list(br["home"]["reasons"]),
            away_factors=list(br["away"]["reasons"]),
        )
        adjusted = apply_adjustments(base_diff, adj)
        expected = _pick_from_diff(adjusted, can_draw=True, home_power=hp, away_power=ap)
        pick_probs = {"home": "1", "draw": "3", "away": "2"}[max(probs, key=probs.get)]

        ins = pred["insight"]
        verdict = str(ins["verdict"])
        lead = str(ins.get("leadSummary", ""))
        detail_text = str(ins.get("scoreSummary", ""))

        row = {
            "match": f"{home_nl} – {away_nl}",
            "base_diff": base_diff,
            "adjusted_diff": adjusted,
            "pick": pick,
            "probs": probs,
            "verdict": verdict,
            "lead": lead,
            "score_summary": detail_text,
        }
        rows.append(row)

        tag = row["match"]

        if pick != expected:
            issues.append(f"{tag}: pick {_pick_label(pick)} != regel {_pick_label(expected)} (adj diff {adjusted:+d})")

        if pick_probs != pick:
            issues.append(
                f"{tag}: pick {_pick_label(pick)} maar hoogste kans {_pick_label(pick_probs)} "
                f"({probs})"
            )

        winner_nl = _verdict_team(pick, home_nl, away_nl)
        if pick == "3":
            if "gelijkspel" not in verdict.lower():
                issues.append(f"{tag}: pick gelijk maar verdict noemt geen gelijkspel")
        elif winner_nl and winner_nl.lower() not in verdict.lower():
            issues.append(f"{tag}: pick {_pick_label(pick)} maar verdict vermeldt '{winner_nl}' niet")

        if SCORE_IN_LEAD.search(lead):
            issues.append(f"{tag}: cijfers/wedstrijdscore in zichtbare lead")

        if _lead_implies_other_winner(lead, pick, home_nl, away_nl):
            issues.append(f"{tag}: lead spreekt tegen pick ({lead[:80]}…)")

        if pick == "3" and ("opent het wk" in lead.lower() or "openingsduel" in lead.lower()):
            issues.append(f"{tag}: lead met openingsdruk bij gelijk-pick")

        if not _note_covers_pick(pick, detail_text, diff=adjusted, home_power=hp, away_power=ap):
            issues.append(f"{tag}: scoreSummary mist toelichting bij deze pick-regel")

        if pick == "3" and abs(adjusted) >= GROUP_DRAW_DIFF_CLEAR_MIN and abs(hp - ap) >= GROUP_DRAW_BASE_CLEAR_GAP:
            issues.append(
                f"{tag}: gelijk-pick maar grote basis+score gap (basis {abs(hp-ap)}, diff {adjusted:+d})"
            )

    draws = sum(1 for r in rows if r["pick"] == "3")
    by_pick = {"1": 0, "2": 0, "3": 0}
    for r in rows:
        by_pick[str(r["pick"])] += 1

    summary = {
        "matches": len(rows),
        "picks": by_pick,
        "draw_pct": round(100 * draws / len(rows), 1),
        "issue_count": len(issues),
        "issues": issues,
    }
    OUT.write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if issues:
        print(f"\n{len(issues)} issue(s), zie {OUT.name}")
        for line in issues:
            print(" -", line)
        return 1
    print(f"\nOK: {len(rows)} groepsduels, pick/kansen/tekst consistent. JSON: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
