from app.predictions import predict_match, team_insight


def test_team_insight_includes_style_and_group_context() -> None:
    insight = team_insight("Korea Republic")
    assert insight is not None
    assert insight["style"]
    assert "Speelstijl" not in insight["summary"]
    context = insight["groupContext"]
    assert isinstance(context, list)
    assert len(context) >= 1
    assert any("Tsjech" in line or "thuis" in line.lower() for line in context)


def test_team_summary_uses_dutch_country_name() -> None:
    insight = team_insight("South Africa")
    assert insight is not None
    assert insight["team"] == "Zuid-Afrika"
    assert "Zuid-Afrika" in insight["summary"]
    assert "South Africa" not in insight["summary"]
    assert insight["tier"] == "Underdog"
    assert insight["powerScore"] == 66
    assert "outsider" not in insight["tier"].lower()


def test_tier_ladder_labels() -> None:
    from app.predictions import (
        TEAM_PROFILES,
        TIER_FAVORIET,
        TIER_SUBTOPPER,
        TIER_TOPFAVORIET,
        TIER_UNDERDOG,
        TIER_VERRASSINGS_PLOEG,
    )

    tiers = {profile.tier for profile in TEAM_PROFILES.values()}
    assert tiers == {
        TIER_TOPFAVORIET,
        TIER_FAVORIET,
        TIER_SUBTOPPER,
        TIER_UNDERDOG,
        TIER_VERRASSINGS_PLOEG,
    }


def test_even_group_match_predicts_draw_with_highest_draw_chance() -> None:
    prediction = predict_match("Korea Republic", "Czechia", "group", "1", "A")
    assert prediction["pick"] == "3"
    draw = prediction["drawProbability"]
    home = prediction["homeWinProbability"]
    away = prediction["awayWinProbability"]
    assert draw is not None and home is not None and away is not None
    assert draw >= home
    assert draw >= away
    assert home + draw + away == 100


def test_match_explanation_uses_dutch_country_names() -> None:
    prediction = predict_match("Mexico", "South Africa", "group", "1", "A")
    text = prediction["explanation"] + " " + prediction["insight"]["narrative"]
    assert "Mexico" in text
    assert "Zuid-Afrika" in text
    assert "South Africa" not in text
