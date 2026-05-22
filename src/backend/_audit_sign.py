import re
from app.data.teams.team_loader import load_all_bundles
from app.data.teams.context_score import match_context_breakdown
from app.teams import fifa_team_key, display_team_name

POS = re.compile(r"\b(profiteert|voordeel|past bij|sterker|hoger)\b", re.I)
NEG = re.compile(r"\b(lastig|kwetsbaar|risico|zwakker|moeite|verstoort|frustreren)\b", re.I)

bundles = load_all_bundles()
issues = []
for fifa, b in bundles.items():
    for opp in b.group_stage.opponents_fifa:
        ok = fifa_team_key(opp)
        if ok not in bundles:
            continue
        br = match_context_breakdown(fifa, ok)
        for side_key in ("home", "away"):
            s = br[side_key]
            team = s["team"]
            for r in s["reasons"]:
                d = int(r["delta"])
                if d == 0:
                    continue
                text = r["reason"]
                pos, neg = bool(POS.search(text)), bool(NEG.search(text))
                if d > 0 and neg and not pos:
                    issues.append((f"{team} vs {display_team_name(opp)}", r["id"], d, text[:80], "pos_text_neg_delta"))
                if d < 0 and pos and not neg:
                    issues.append((f"{team} vs {display_team_name(opp)}", r["id"], d, text[:80], "neg_delta_pos_text"))

print("mismatches", len(issues))
for row in issues[:25]:
    print(row)
