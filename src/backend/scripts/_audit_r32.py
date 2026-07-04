from app.match_results_store import load_results
from app.tournament import build_tournament_view

t = build_tournament_view()
r32 = [m for m in t["knockoutMatches"] if m["round"] == "Round of 32"]
r16 = [m for m in t["knockoutMatches"] if m["round"] == "Round of 16"]
print("R32 completed", sum(1 for m in r32 if m["status"] == "completed"), "/", len(r32))
print("R16 teams known", sum(1 for m in r16 if m["homeTeam"] != "Onbekend"), "/", len(r16))
print()
print("R32 audit:")
correct = 0
total = 0
for m in sorted(r32, key=lambda x: x["matchNumber"]):
    if m["status"] != "completed":
        continue
    total += 1
    sc = m["score"]
    actual = "1" if sc["home"] > sc["away"] else ("3" if sc["home"] == sc["away"] else "2")
    pick = m["aiPrediction"]["pick"]
    sug = m["aiPrediction"].get("suggestedScore")
    ss = f"{sug['home']}-{sug['away']}" if sug else "-"
    score_ok = sug and sug["home"] == sc["home"] and sug["away"] == sc["away"]
    if pick == actual:
        correct += 1
    print(
        f"  {m['matchNumber']:3} {m['homeTeam'][:14]:14} {sc['home']}-{sc['away']} "
        f"{m['awayTeam'][:14]:14} pred={pick} actual={actual} voorsp={ss} "
        f"{'PICK OK' if pick == actual else 'PICK MISS'} "
        f"{'SCORE EXACT' if score_ok else ''}"
    )
print(f"\nPick accuracy: {correct}/{total}")
print("\nR16:")
for m in sorted(r16, key=lambda x: x["matchNumber"]):
    sug = m["aiPrediction"].get("suggestedScore")
    print(
        f"  {m['matchNumber']} {m['homeTeam']} vs {m['awayTeam']} "
        f"pick={m['aiPrediction']['pick']} sug={sug}"
    )
