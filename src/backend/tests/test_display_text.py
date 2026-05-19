from app.display_text import humanize_factor_reason, humanize_research_line, humanize_team_spark


def test_zwakwer_becomes_plain_dutch() -> None:
    text = humanize_factor_reason(
        "Tegenstander kwetsbaar: Zwakwer Mexico Giménez/Jiménez.",
        factor_id="opponent_profile_weak",
        subject_team="Mexico",
        opponent_team="Zuid-Afrika",
    )
    assert "Zwakwer" not in text
    assert "Giménez" in text


def test_style_matchup_is_readable() -> None:
    text = humanize_factor_reason(
        "Omschakeling/transities passen tegen compact Zuid-Afrika",
        factor_id="style_matchup",
        subject_team="Mexico",
        opponent_team="Zuid-Afrika",
    )
    assert "omschakeling" in text.lower()
    assert "compact" in text.lower()


def test_humanize_team_spark_lopetegui() -> None:
    text = humanize_team_spark(
        "Julen Lopetegui op Qatar , Spaans possession-model in woestijn-federatie.",
        "Qatar",
    )
    assert "bondscoach" in text.lower()
    assert "Qatar" in text
    assert "woestijn" not in text.lower()
    assert "possession" not in text.lower()
    assert "compacte ploeg" in text.lower()
    assert "bond" not in text.lower().replace("bondscoach", "")


def test_humanize_team_spark_son() -> None:
    text = humanize_team_spark(
        "Son Heung-min vierde WK onder nieuwe coach Hong Myung-bo (legend).",
        "Zuid-Korea",
    )
    assert "bondscoach" in text.lower()
    assert "Son" in text


def test_simons_absence_is_not_parsed_as_japan_star() -> None:
    text = humanize_factor_reason(
        "Japan opener zonder Simons.",
        factor_id="psychology",
        subject_team="Nederland",
        opponent_team="Japan",
    )
    assert "Xavi Simons" in text
    assert "Japan leunt" not in text
    assert "Nederland" in text

    text_jp = humanize_factor_reason(
        "NL opener Simons absent → ruimte?",
        factor_id="psychology",
        subject_team="Japan",
        opponent_team="Nederland",
    )
    assert "Xavi Simons" in text_jp
    assert "Japan leunt" not in text_jp


def test_humanize_england_tuchel_with_dutch_opponent_name() -> None:
    text = humanize_factor_reason(
        "England Tuchel.",
        factor_id="matchup_risk",
        subject_team="Ghana",
        opponent_team="Engeland",
    )
    assert "Tuchel" in text
    assert "Ghana" in text
    assert "Engeland" in text
    assert len(text.split()) >= 8


def test_humanize_ecuador_caicedo_matchup_risk() -> None:
    text = humanize_factor_reason(
        "Ecuador Caicedo.",
        factor_id="matchup_risk",
        subject_team="Ivoorkust",
        opponent_team="Ecuador",
    )
    assert "Caicedo" in text
    assert "middenveld" in text.lower()
    assert "Ivoorkust" in text
    assert text.lower() != "tegen ecuador: caicedo."


def test_humanize_short_colon_underdog() -> None:
    text = humanize_research_line("Tsjechië: Underdog.", opponent_nl="Tsjechië")
    assert "underdog" in text.lower()
    assert "Tsjechië" in text
    assert ":" not in text or "geldt" in text


def test_mexico_cohost_crowd_not_against_itself() -> None:
    text = humanize_factor_reason(
        "Co-host: Mexico City opener ≈2240m met massaal thuispubliek.",
        factor_id="cohost_crowd",
        subject_team="Mexico",
        opponent_team="Zuid-Afrika",
    )
    assert "tegen co-host Mexico" not in text
    assert "Mexico" in text
    assert "thuis" in text.lower() or "publiek" in text.lower()


def test_humanize_netherlands_japan_moriyasu_press() -> None:
    text = humanize_factor_reason(
        "Japan Moriyasu press.",
        factor_id="matchup_risk",
        subject_team="Nederland",
        opponent_team="Japan",
    )
    assert "Moriyasu" in text
    assert "Japan" in text
    assert "Nederland" in text
    assert "druk" in text.lower() or "press" in text.lower()
    assert "Japan Moriyasu press." not in text


def test_humanize_japan_style_press_vs_netherlands() -> None:
    text = humanize_factor_reason(
        "Eigen press kan compact blok Nederland onder druk zetten",
        factor_id="style_matchup",
        subject_team="Japan",
        opponent_team="Nederland",
    )
    assert "Japan" in text
    assert "Nederland" in text
    assert "opbouw" in text.lower()
    assert "lage blok" not in text.lower()


def test_humanize_japan_fixture_story_moriyasu() -> None:
    text = humanize_factor_reason(
        "Moriyasu-press tegen compact Oranje",
        factor_id="fixture_story",
        subject_team="Japan",
        opponent_team="Nederland",
    )
    assert "Moriyasu" in text
    assert "Japan" in text
    assert "Oranje" in text or "Nederland" in text


def test_parentheses_club_and_age() -> None:
    text = humanize_research_line("James (Minnesota) geselecteerd ondanks arm-fit.")
    assert "club Minnesota" in text or "Minnesota" in text
    assert "schouder" in text.lower() or "blessure" in text.lower()
