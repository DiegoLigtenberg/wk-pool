"""Print zichtbare voorspellingsteksten (verdict + lead) voor alle groepsduels."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()

import json
import re
import sys
from pathlib import Path

from app.data.teams.team_loader import load_all_bundles
from app.predictions import predict_match
from app.teams import display_team_name, fifa_team_key

OUT = Path(__file__).resolve().parent / "audit_lead_summaries.json"

SCORE_IN_LEAD = re.compile(
    r"wedstrijdscore|\d+\s*–\s*\d+|\d+\s+punten",
    re.I,
)
BROKEN_HOST = re.compile(r"speelt thuis in \w+ opent", re.I)
AWAY_COHOST = re.compile(
    r"(Zuid-Afrika|Haïti|Tsjechië|Zuid-Korea|Schotland|Bosnië).{0,20}opent als co-host",
    re.I,
)


def _duels() -> list[tuple[str, str]]:
    bundles = load_all_bundles()
    pairs: list[tuple[str, str]] = []
    for fifa, bundle in bundles.items():
        for opp in bundle.group_stage.opponents_fifa:
            key = fifa_team_key(opp)
            if key in bundles:
                pairs.append((fifa, key))
    return sorted(pairs)


def _flags(lead: str, verdict: str) -> list[str]:
    visible = f"{verdict} {lead}"
    flags: list[str] = []
    if SCORE_IN_LEAD.search(visible):
        flags.append("cijfers_in_zichtbare_tekst")
    if BROKEN_HOST.search(lead):
        flags.append("dubbele_thuis_opent_zin")
    if AWAY_COHOST.search(lead):
        flags.append("uitploeg_als_cohost")
    if lead.count("opent als co-host") >= 2:
        flags.append("herhaalde_cohost_opener")
    if "Let op:" in lead and lead.split("Let op:")[-1].strip().startswith(
        lead.split(".")[0].split()[-1] if "." in lead else ""
    ):
        pass
    if len(lead) < 30:
        flags.append("te_kort")
    return flags


def main() -> int:
    rows: list[dict] = []
    problem_count = 0
    for home, away in _duels():
        pred = predict_match(home, away, "group", "1", None)
        ins = pred["insight"]
        verdict = str(ins["verdict"])
        lead = str(ins.get("leadSummary") or ins["steps"][1]["body"])
        score = str(ins.get("scoreSummary", ""))
        flags = _flags(lead, verdict)
        if flags:
            problem_count += 1
        rows.append(
            {
                "match": f"{display_team_name(home)} – {display_team_name(away)}",
                "pick": pred["pick"],
                "verdict": verdict,
                "leadSummary": lead,
                "scoreSummary": score,
                "flags": flags,
            }
        )

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Totaal duels: {len(rows)}")
    print(f"Met flags: {problem_count}")
    print(f"JSON: {OUT}\n")

    for row in rows:
        if row["flags"]:
            print(f"[{', '.join(row['flags'])}] {row['match']}")
            print(f"  verdict: {row['verdict']}")
            print(f"  lead:    {row['leadSummary']}\n")

    print("--- Alle zichtbare leads (verdict + leadSummary) ---\n")
    for row in rows:
        print(row["match"])
        print(f"  {row['verdict']}")
        print(f"  {row['leadSummary']}")
        print()

    return 1 if problem_count else 0


if __name__ == "__main__":
    sys.exit(main())
