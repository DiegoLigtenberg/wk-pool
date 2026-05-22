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
    assert "staat bij ons als" in insight["summary"]
    assert insight["tier"] == "Underdog"
    assert insight["powerScore"] == 66
    assert "outsider" not in insight["tier"].lower()


def test_team_insight_niche_is_not_duplicate_of_distinctive_spark() -> None:
    insight = team_insight("South Africa")
    assert insight is not None
    spark = insight["distinctiveSpark"]
    niche = insight["niche"]
    assert spark and niche
    normalized_spark = spark.replace(" ", "").lower()
    assert not any(n.replace(" ", "").lower() == normalized_spark for n in niche)


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


def test_even_group_match_pick_aligned_with_probs() -> None:
    prediction = predict_match("Korea Republic", "Czechia", "group", "1", "A")
    pick = prediction["pick"]
    probs = {
        "1": prediction["homeWinProbability"],
        "3": prediction["drawProbability"],
        "2": prediction["awayWinProbability"],
    }
    assert pick == max(probs, key=lambda k: probs[k] or 0)
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
