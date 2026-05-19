"""Context-breakdown redenen worden voor de UI gehumaniseerd."""

from app.data.teams.context_score import match_context_breakdown, side_context
from app.teams import fifa_team_key


def test_ivory_coast_ecuador_caicedo_reason_is_readable() -> None:
    br = match_context_breakdown(
        fifa_team_key("Côte d'Ivoire"), fifa_team_key("Ecuador")
    )
    home = br["home"]
    reasons = {r["id"]: r["reason"] for r in home["reasons"]}
    assert "matchup_risk" in reasons
    assert "Caicedo" in reasons["matchup_risk"]
    assert "middenveld" in reasons["matchup_risk"].lower()
    assert reasons["matchup_risk"].lower() != "tegen ecuador: caicedo."


def test_netherlands_japan_simons_only_in_group_factors() -> None:
    ctx = side_context(fifa_team_key("Netherlands"), fifa_team_key("Japan"))
    simons_lines = [
        f.reason for f in ctx.factors if "simons" in f.reason.lower()
    ]
    assert len(simons_lines) == 1
    assert ctx.factors[0].id == "squad_load" or any(
        f.id == "squad_load" for f in ctx.factors if "simons" in f.reason.lower()
    )

    br = match_context_breakdown(
        fifa_team_key("Netherlands"), fifa_team_key("Japan")
    )
    home_reasons = br["home"]["reasons"]
    simons_ui = [r for r in home_reasons if "simons" in r["reason"].lower()]
    assert len(simons_ui) == 1
    for reason in home_reasons:
        if reason["id"] == "psychology":
            assert "simons" not in reason["reason"].lower()


def test_iraq_senegal_bank_note_is_readable() -> None:
    br = match_context_breakdown(fifa_team_key("Iraq"), fifa_team_key("Senegal"))
    home = br["home"]
    texts = " ".join(r["reason"] for r in home["reasons"]).lower()
    assert "senegal" in texts
    assert len(texts.split()) > 12
