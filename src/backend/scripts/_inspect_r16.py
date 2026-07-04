"""Inspect R16 predictions: diff, adjustments, R32 form."""
from app.group_form import build_group_form_index
from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.knockout_form import build_knockout_round_form_index
from app.match_results_store import load_results
from app.predictions import predict_match
from app.tournament import load_fixtures

fixtures = load_fixtures()
store = load_results()
bracket = build_knockout_bracket_state(fixtures, store)
form = build_group_form_index(fixtures, store)
ko = build_knockout_round_form_index(fixtures, store, bracket.resolved_teams, before_round="Round of 16")

for fx in sorted(fixtures, key=lambda f: f.match_number):
    if fx.round_number != "Round of 16":
        continue
    h, a = resolve_knockout_teams(fx, bracket)
    gf = (form.get(h), form.get(a))
    kf = (ko.get(h), ko.get(a))
    p = predict_match(h, a, "knockout", fx.round_number, None, match_number=fx.match_number, group_forms=gf, knockout_forms=kf)
    adj = p.get("insight", {}).get("poolAdjustments", [])
    hf, af = gf
    hk, ak = kf
    print(f"\n=== {fx.match_number} {h} vs {a} ===")
    print(f"pick={p['pick']} score={p.get('suggestedScore', {}).get('home')}-{p.get('suggestedScore', {}).get('away')} conf={p['confidence']}")
    if hf and hk:
        print(f"  {h}: poule gpg={hf.goals_per_game:.2f} R32 gpg={hk.goals_per_game:.2f} R32={hk.goals_for}-{hk.goals_against}")
    if af and ak:
        print(f"  {a}: poule gpg={af.goals_per_game:.2f} R32 gpg={ak.goals_per_game:.2f} R32={ak.goals_for}-{ak.goals_against}")
    for a_item in adj[:6]:
        print(f"  adj: {a_item.get('label')} ({a_item.get('delta'):+d})")
