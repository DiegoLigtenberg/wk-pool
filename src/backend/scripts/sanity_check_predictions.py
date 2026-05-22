"""Sanity: voorspellingen vs research-ranking (geen live odds)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()

from app.data.teams.team_loader import load_all_bundles
from app.predictions import predict_match

# Verwachte richting uit research power_score + context (geen externe odds).
CHECKS = [
    ("USA", "Paraguay", "group", "1", "thuis favoriet (co-host)"),
    ("Argentina", "Haiti", "group", "1", "thuis grote favoriet"),
    ("France", "Brazil", "group", "1", "topduel, vaak gelijk of licht"),
    ("Qatar", "Switzerland", "group", "2", "uit favoriet Zwitserland"),
    ("Morocco", "Brazil", "group", "2", "uit favoriet Brazilië"),
    ("Korea Republic", "Czechia", "group", "3", "gelijkwaardig"),
    ("Mexico", "South Africa", "group", "1", "thuis favoriet"),
    ("Spain", "Japan", "group", "1", "thuis favoriet"),
    ("Germany", "Curaçao", "group", "1", "thuis grote favoriet"),
    ("Netherlands", "Uzbekistan", "group", "1", "thuis grote favoriet"),
]


def main() -> int:
    bundles = load_all_bundles()
    top = sorted(bundles.values(), key=lambda b: b.power_score, reverse=True)[:8]
    print("Top basisscores:", ", ".join(f"{b.team_name_nl} ({b.power_score})" for b in top))
    print()
    print(f"{'Wedstrijd':<28} {'diff':>5} {'pick':>4} {'H-G-U':>12} {'conf':>4}  Verwacht")
    print("-" * 85)

    ok = 0
    for home, away, stage, pick_exp, note in CHECKS:
        pred = predict_match(home, away, stage, "1", "X")
        pick = pred["pick"]
        h, d, a = pred["homeWinProbability"], pred["drawProbability"], pred["awayWinProbability"]
        probs = f"{h}-{d or 0}-{a}"
        diff = pred["insight"]["diff"]
        match = pick == pick_exp
        ok += int(match)
        flag = "OK" if match else "??"
        print(
            f"{home} - {away:<12} {diff:+5} {pick:>4} {probs:>12} {pred['confidence']:>3}%  "
            f"{note} [{flag}]"
        )

    print()
    print(f"Richting klopt bij {ok}/{len(CHECKS)} handmatige checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
