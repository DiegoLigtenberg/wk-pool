"""Paar-analyse groepsduel uit beide YAML-dossiers."""

from app.data.teams.context_scoring_builder import build_versus_factors
from app.data.teams.team_loader import get_team_bundle, load_all_bundles


def test_mexico_south_africa_includes_tactical_pairwise() -> None:
    bundles = load_all_bundles()
    mexico = bundles["Mexico"]
    south_africa = bundles["South Africa"]
    factors = build_versus_factors(mexico, "South Africa", opponent=south_africa)
    ids = {f.id for f in factors}
    assert ids & {"style_matchup", "opponent_profile_weak", "home_fixture", "matchup_edge", "opener_context"}
    reasons = " ".join(f.reason for f in factors).lower()
    assert (
        "compact" in reasons
        or "giménez" in reasons
        or "broos" in reasons
        or "hoogte" in reasons
        or "2240" in reasons
        or "opener" in reasons
    )
