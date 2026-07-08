"""Honest breakdown: QF picks, diff, adjustments, probabilities."""
from app.group_form import build_group_form_index
from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.knockout_form import build_knockout_round_form_index
from app.data.teams.context_score import match_context_breakdown
from app.match_results_store import load_results
from app.predictions import predict_match
from app.pool_edge import collect_pick_adjustments, apply_adjustments
from app.teams import fifa_team_key
from app.tournament import load_fixtures

fixtures = load_fixtures()
store = load_results()
bracket = build_knockout_bracket_state(fixtures, store)
form = build_group_form_index(fixtures, store)
ko = build_knockout_round_form_index(fixtures, store, bracket.resolved_teams, before_round="Quarter Finals")

for fx in sorted(fixtures, key=lambda f: f.match_number):
    if fx.round_number != "Quarter Finals":
        continue
    h, a = resolve_knockout_teams(fx, bracket)
    hk, ak = fifa_team_key(h), fifa_team_key(a)
    bd = match_context_breakdown(hk, ak)
    base = int(bd["diff"])
    gf = (form.get(h), form.get(a))
    kf = (ko.get(h), ko.get(a))
    home_form, away_form = gf
    from app.group_form import live_form_tuple
    from app.pool_edge import live_form_from_group_played_yaml

    live = live_form_tuple(home_form, away_form) if home_form and away_form else None
    adjs = collect_pick_adjustments(
        home_key=hk,
        away_key=ak,
        home_power=int(bd["home"]["powerScore"]),
        away_power=int(bd["away"]["powerScore"]),
        home_factors=list(bd["home"]["reasons"]),
        away_factors=list(bd["away"]["reasons"]),
        live_form=live,
        include_live_form=True,
        home_form=home_form,
        away_form=away_form,
    )
    adj_diff = apply_adjustments(base, adjs)
    pred = predict_match(h, a, "knockout", fx.round_number, None, match_number=fx.match_number, group_forms=gf, knockout_forms=kf)
    sug = pred.get("suggestedScore", {})
    print(f"\n{'='*55}")
    print(f"{fx.match_number} {h} vs {a}")
    print(f"  Research diff: {base:+d}  ->  adjusted: {adj_diff:+d}")
    print(f"  Pick {pred['pick']}  |  P(1)={pred['homeWinProbability']}%  P(X)={pred['drawProbability']}%  P(2)={pred['awayWinProbability']}%  conf={pred['confidence']}%")
    print(f"  Suggested 90min: {sug.get('home')}-{sug.get('away')}")
    if kf[0]:
        print(f"  {h} KO so far: {kf[0].goals_for}-{kf[0].goals_against} in {kf[0].played} game(s)")
    if kf[1]:
        print(f"  {a} KO so far: {kf[1].goals_for}-{kf[1].goals_against} in {kf[1].played} game(s)")
    print("  Adjustments:")
    for x in adjs:
        print(f"    {x.delta:+d}  {x.label}")
