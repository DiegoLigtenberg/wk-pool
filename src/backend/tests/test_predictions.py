from app.predictions import predict_match, team_insight


def test_team_summary_uses_dutch_country_name() -> None:
    insight = team_insight("South Africa")
    assert insight is not None
    assert "Zuid-Afrika" in insight["summary"]
    assert "South Africa" not in insight["summary"]
    assert insight["tier"] == "Underdog"
    assert "outsider" not in insight["tier"].lower()


def test_tier_labels_avoid_vague_outsider_term() -> None:
    from app.predictions import TEAM_PROFILES

    tiers = {profile.tier for profile in TEAM_PROFILES.values()}
    assert "Outsider" not in tiers
    assert "Sterke outsider" not in tiers
    assert "Betrouwbare outsider" not in tiers


def test_match_explanation_uses_dutch_country_names() -> None:
    prediction = predict_match("Mexico", "South Africa", "group", "1", "A")
    explanation = prediction["explanation"]
    assert "Mexico" in explanation or "Zuid-Afrika" in explanation
    assert "South Africa" not in explanation
    assert "Zuid-Afrika" in explanation
