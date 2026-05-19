from app.predictions import predict_match


def test_qatar_switzerland_verdict_is_readable() -> None:
    pred = predict_match("Qatar", "Switzerland", "group", "1", "B")
    assert pred["pick"] == "2"
    insight = pred["insight"]
    verdict = str(insight["verdict"])
    steps = insight["steps"]
    joined = verdict + " " + " ".join(s["body"] for s in steps)
    assert verdict == "De AI voorspelt dat Zwitserland wint."
    assert "79" not in verdict
    assert "67" not in verdict
    assert steps[0]["title"] == "Hoe dit werkt"
    assert "ai-model" in steps[0]["body"].lower()
    assert "Qatar" in steps[0]["body"]
    assert "Zwitserland" in steps[0]["body"]
    assert steps[1]["title"] == "Belangrijk in dit duel"
    assert "ondersteunt de voorspelling" not in steps[1]["body"].lower()
    assert "Vanuit Qatar" not in joined


def test_even_match_intro_does_not_claim_leader() -> None:
    pred = predict_match("Korea Republic", "Czechia", "group", "1", "A")
    intro = pred["insight"]["steps"][0]["body"]
    assert pred["pick"] == "3"
    assert "hoger" not in intro.lower()
    assert "71" in intro
    assert intro.count("71") >= 2


def test_netherlands_narrative_has_no_english_lean() -> None:
    pred = predict_match("Netherlands", "Japan", "group", "1", "E")
    narrative = pred["insight"]["steps"][1]["body"].lower()
    assert " lean " not in f" {narrative} "
    assert "steunt" in narrative or "basissterkte" in narrative


def test_mexico_prediction_uses_research_not_generic_strengths() -> None:
    pred = predict_match("Mexico", "South Africa", "group", "1", "A")
    components = pred["insight"]["steps"][1]["body"]
    assert "publieksenergie" not in components
    assert "ondersteunt de voorspelling" not in components.lower()
    assert "Componenten die in deze wedstrijd meetellen" not in components
    assert "co-host" in components.lower() or "thuis" in components.lower()
    assert len(pred["insight"]["steps"]) == 2
    insight = pred["insight"]
    assert insight["home"]["effectiveScore"] > insight["away"]["effectiveScore"]
    match_factors = [
        f for f in insight["home"]["factors"] if f["scope"] == "match" and f["delta"] != 0
    ]
    assert match_factors
    assert "Mexico:" not in components
    assert "Zuid-Afrika:" not in components
    assert "Zwakwer" not in components
    assert "Tegenstander kwetsbaar" not in components
    low = components.lower()
    assert (
        "giménez" in low
        or "compact" in low
        or "hoogte" in low
        or "2240" in low
        or "thuisvoordeel als co-host" in low
    )
