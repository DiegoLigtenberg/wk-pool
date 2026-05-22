"""Geen dubbele opener/tactiek in context_scoring."""

from app.data.teams.context_scoring_builder import build_context_scoring, build_versus_factors
from app.data.teams.context_score import match_context_breakdown
from app.data.teams.team_loader import load_all_bundles
from app.predictions import predict_match
from app.teams import fifa_team_key


def test_opener_context_only_on_opener_fixture() -> None:
    bundles = load_all_bundles()
    for team_key in ("South Africa", "Mexico"):
        bundle = bundles[team_key]
        opener_opp = min(
            bundle.group_stage.fixtures, key=lambda f: f.match_number
        ).opponent_fifa
        for opp in bundle.group_stage.opponents_fifa:
            factors = build_versus_factors(
                bundle, opp, opponent=bundles[fifa_team_key(opp)]
            )
            has_opener = any(f.id == "opener_context" for f in factors)
            if fifa_team_key(opp) == fifa_team_key(opener_opp):
                assert has_opener, f"{team_key} opener vs {opp} mist opener_context"
            else:
                assert not has_opener, f"{team_key} vs {opp} heeft ten onrechte opener_context"


def test_no_double_positive_style_in_breakdown() -> None:
    bundles = load_all_bundles()
    for fifa, bundle in bundles.items():
        for opp in bundle.group_stage.opponents_fifa:
            opp_key = fifa_team_key(opp)
            if opp_key not in bundles:
                continue
            br = match_context_breakdown(fifa, opp_key)
            for side in (br["home"], br["away"]):
                plus_styles = [
                    r
                    for r in side["reasons"]
                    if r["id"] == "style_matchup" and r["delta"] > 0
                ]
                assert len(plus_styles) <= 1, (
                    f"{side['team']}: {len(plus_styles)}x +1 style_matchup"
                )


def test_mexico_south_africa_no_duplicate_cohost_factor_text() -> None:
  pred = predict_match("Mexico", "South Africa", "group", "1", "A")
  home = pred["insight"]["home"]
  reasons = {
      str(f["reason"]).strip().lower()
      for f in home["factors"]
      if f.get("delta") and str(f.get("reason", "")).strip()
  }
  cohost_lines = [
      f
      for f in home["factors"]
      if f.get("delta")
      and str(f.get("id")) in {"cohost_crowd", "home_fixture"}
  ]
  assert len(cohost_lines) <= 1, [
      (f["id"], f["delta"], f.get("reason")) for f in cohost_lines
  ]
  assert not any(
      "mexico opent als co-host" in r and "zuid-afrika" in r for r in reasons
  )


def test_south_africa_opener_not_in_persistent() -> None:
    bundles = load_all_bundles()
    scoring = build_context_scoring(bundles["South Africa"], bundles)
    assert not any(f.id == "distinctive_spark" for f in scoring.persistent)
    mexico_factors = scoring.versus[fifa_team_key("Mexico")]
    assert any(f.id == "opener_context" for f in mexico_factors)
