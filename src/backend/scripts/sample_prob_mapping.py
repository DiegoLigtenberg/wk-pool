from app.predictions import predict_match, _probabilities
from app.data.teams.context_score import match_context_breakdown
from app.teams import fifa_team_key

pairs = [
    ("USA", "Paraguay"),
    ("Argentina", "Haiti"),
    ("Korea Republic", "Czechia"),
    ("France", "Brazil"),
    ("Morocco", "Brazil"),
    ("Côte d'Ivoire", "Ecuador"),
    ("Mexico", "South Africa"),
]

print("diff | basis | ctx H/A | pick | H-D-A | conf")
for h, a in pairs:
    br = match_context_breakdown(fifa_team_key(h), fifa_team_key(a))
    p = predict_match(h, a, "group", "1", "A")
    d = br["diff"]
    bh, ba = br["home"]["powerScore"], br["away"]["powerScore"]
    ch, ca = br["home"]["contextDelta"], br["away"]["contextDelta"]
    probs = f"{p['homeWinProbability']}-{p['drawProbability']}-{p['awayWinProbability']}"
    print(f"{d:+3} | {bh}-{ba} | {ch:+d}/{ca:+d} | {p['pick']} | {probs} | {p['confidence']}%")

print("\nPick = hoogste kans (gelijk boost bij |diff|<=2)")
print("\nGroeps-kansencurve (logistic op diff):")
for d in [-12, -8, -4, -2, 0, 2, 4, 8, 12]:
    pr = _probabilities(d, True)
    print(f"  diff {d:+3}: {pr['home']}-{pr['draw']}-{pr['away']}")
