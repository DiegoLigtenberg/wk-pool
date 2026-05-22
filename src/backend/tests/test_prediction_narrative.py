import re

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
    lead = str(insight.get("leadSummary") or steps[1]["body"])
    assert "wedstrijdscore" not in lead.lower()
    assert "13 punten" not in lead
    assert "verschil in wedstrijdscore" not in lead.lower()
    assert "op papier" in lead.lower() or "lopetegui" in lead.lower() or "compact" in lead.lower()
    assert "ondersteunt de voorspelling" not in steps[1]["body"].lower()
    assert "Vanuit Qatar" not in joined
    assert "wedstrijdscore" in str(insight["scoreSummary"]).lower()


def test_even_match_intro_does_not_claim_leader() -> None:
    pred = predict_match("Korea Republic", "Czechia", "group", "1", "A")
    intro = pred["insight"]["steps"][0]["body"]
    assert pred["pick"] == "3"
    assert "hoger" not in intro.lower()
    assert "wedstrijdscore" in intro.lower()
    assert "71" not in intro


def test_netherlands_narrative_has_no_english_lean() -> None:
    pred = predict_match("Netherlands", "Japan", "group", "1", "E")
    narrative = pred["insight"]["steps"][1]["body"].lower()
    assert " lean " not in f" {narrative} "
    assert any(w in narrative for w in ("simons", "omschakeling", "moriyasu", "japan", "compact"))


def test_mexico_opener_lead_is_grammatical_dutch() -> None:
    """Openingsduel Mexico–Zuid-Afrika: geen dubbele thuis-zin, uitploeg geen co-host."""
    pred = predict_match("Mexico", "South Africa", "group", "1", "A")
    lead = str(pred["insight"].get("leadSummary") or pred["insight"]["steps"][1]["body"])
    verdict = str(pred["insight"]["verdict"])
    visible = f"{verdict} {lead}".lower()
    assert "speelt thuis in mexico opent" not in visible
    assert "zuid-afrika opent als co-host" not in visible
    assert "wedstrijdscore" not in visible
    assert re.search(r"\d+\s*–\s*\d+", visible) is None
    assert "mexico" in visible and "co-host" in visible
    assert "let op" not in lead.lower()
    assert lead.lower().count("mexico city") <= 1


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
        f
        for f in (insight["home"]["factors"] + insight["away"]["factors"])
        if f["scope"] == "match" and f["delta"] != 0
    ]
    assert match_factors
    assert "Mexico:" not in components
    assert "Zuid-Afrika:" not in components
    assert "Zwakwer" not in components
    assert "Tegenstander kwetsbaar" not in components
    low = components.lower()
    assert "thuisvoordeel als co-host" not in low
    assert "weegt zwaarder" not in low
    assert "kleine tactische verschillen" not in low
    assert (
        "giménez" in low
        or "compact" in low
        or "hoogte" in low
        or "2240" in low
        or "toronto" in low
        or "mexico city" in low
        or "co-host" in low
    )


def test_brazil_morocco_narrative_is_complete() -> None:
    pred = predict_match("Brazil", "Morocco", "group", "1", "C")
    why = pred["insight"]["steps"][1]["body"]
    low = why.lower()
    assert "cou." not in low
    assert "ouahbi" in low or "hakimi" in low or "marokko" in low or "brazilië" in low
    assert why.endswith(".")


def test_canada_bosnia_cohost_not_triple_in_factor_cards() -> None:
    pred = predict_match("Canada", "Bosnia and Herzegovina", "group", "1", "I")
    home = pred["insight"]["home"]["factors"]
    cohost_labels = [
        f for f in home if str(f.get("label")) == "co-host" and int(f.get("delta", 0)) > 0
    ]
    assert len(cohost_labels) == 1
    team_cohost = [f for f in home if str(f.get("scope")) == "team" and str(f.get("label")) == "co-host"]
    assert len(team_cohost) == 1


def test_canada_bosnia_pick_home_with_explanation() -> None:
    pred = predict_match("Canada", "Bosnia and Herzegovina", "group", "1", "I")
    assert pred["pick"] in ("1", "3")
    verdict = str(pred["insight"]["verdict"]).lower()
    if pred["pick"] == "1":
        assert "canada wint" in verdict
    else:
        assert "gelijkspel" in verdict
    score = str(pred["insight"].get("scoreSummary", "")).lower()
    assert str(pred["insight"].get("pickLogicNote", "")).strip() == ""
    assert "wedstrijdscore" in score
    if pred["pick"] == "1":
        assert any(w in score for w in ("sterk", "papier", "favoriet", "sterkere", "kansen"))
        assert "punten" in score
    h = int(pred["homeWinProbability"] or 0)
    d = int(pred["drawProbability"] or 0)
    a = int(pred["awayWinProbability"] or 0)
    pick_probs = {"1": h, "2": a, "3": d}
    assert pick_probs[str(pred["pick"])] >= max(h, d, a) - 1


def test_haiti_scotland_lead_tactical_not_duplicate_paper() -> None:
    pred = predict_match("Haiti", "Scotland", "group", "1", None)
    assert pred["pick"] == "2"
    score = str(pred["insight"].get("scoreSummary", "")).lower()
    lead = str(pred["insight"].get("leadSummary", "")).lower()
    assert str(pred["insight"].get("pickLogicNote", "")).strip() == ""
    assert any(w in score for w in ("kansen", "sterk", "papier", "favoriet"))
    assert "op papier de favoriet" not in lead
    assert "counter" in lead or "compact" in lead


def test_canada_bosnia_lead_no_raw_away_fixture() -> None:
    pred = predict_match("Canada", "Bosnia and Herzegovina", "group", "1", "I")
    lead = str(pred["insight"].get("leadSummary", ""))
    assert "heeft last van: Uit tegen" not in lead
    assert "heeft last van: uit tegen" not in lead.lower()


def test_canada_bosnia_narrative_is_concrete() -> None:
    pred = predict_match("Canada", "Bosnia and Herzegovina", "group", "1", "I")
    why = pred["insight"]["steps"][1]["body"]
    low = why.lower()
    assert pred["pick"] in ("1", "3")
    assert "thuisvoordeel als co-host" not in low
    assert "weegt zwaarder" not in low
    assert "kleine tactische verschillen" not in low
    assert any(
        w in low
        for w in ("toronto", "vancouver", "co-host", "opener", "keeper", "st. clair")
    )
