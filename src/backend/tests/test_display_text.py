from app.display_text import (
    clip_research_excerpt,
    humanize_factor_reason,
    humanize_matchup_shorthand,
    humanize_research_line,
    humanize_team_spark,
    looks_truncated_reason,
)


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
    low = text.lower()
    assert "compact" in low
    assert "schakelen" in low or "omschakeling" in low


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


def test_baked_machine_prefix_stripped() -> None:
    text = humanize_factor_reason(
        "In dit duel speelt mee: Zwakker tegen Salah-Egypte counters; "
        "dat vraagt extra aandacht van België.",
        factor_id="tactical_weakness",
        subject_team="België",
        opponent_team="Egypte",
    )
    assert "in dit duel speelt mee" not in text.lower()
    assert "extra aandacht" not in text.lower()
    assert "België" in text
    assert "Egypte" in text


def test_sterk_tegen_readable() -> None:
    text = humanize_factor_reason(
        "Sterk Salah/Marmoush transitions tegen Garcia-België",
        factor_id="opponent_profile_strong",
        subject_team="België",
        opponent_team="Egypte",
    )
    assert "Egypte" in text
    assert "Salah" in text
    assert "in dit duel speelt mee" not in text.lower()


def test_haiti_brazil_group_later() -> None:
    text = humanize_factor_reason(
        "Brazil group later.",
        factor_id="matchup_risk",
        subject_team="Haïti",
        opponent_team="Brazilië",
    )
    assert "Brazilië" in text
    assert "groep" in text.lower()


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


def test_humanize_opponent_profile_weak_argentina_messi() -> None:
    text = humanize_factor_reason(
        "Kwetsbaar als centrum dicht (Algerije/Oostenrijk) en Messi geïsoleerd.",
        factor_id="opponent_profile_weak",
        subject_team="Algerije",
        opponent_team="Argentinië",
    )
    assert "inspelen" in text.lower()
    assert "Argentinië" in text
    assert "Messi" in text
    assert "Algerije" in text


def test_humanize_opponent_profile_weak_uruguay_space() -> None:
    text = humanize_factor_reason(
        "Kwetsbaar ruimte achter druk tegen Spanje.",
        factor_id="opponent_profile_weak",
        subject_team="Spanje",
        opponent_team="Uruguay",
    )
    assert "profiteren" in text.lower()
    assert "Uruguay" in text


def test_humanize_matchup_edge_compact_and_debuut() -> None:
    jordan = humanize_matchup_shorthand(
        "Jordanië compact blok.",
        "Jordanië",
        team_nl="Algerije",
        kind="edge",
    )
    assert "profiteren" in jordan.lower() or "ruimte vinden" in jordan.lower()
    assert "lastig voor Algerije" not in jordan

    debuut = humanize_matchup_shorthand(
        "Curaçao WK-debuut in de groepsopener.",
        "Curaçao",
        team_nl="Duitsland",
        kind="edge",
    )
    assert "favoriet" in debuut.lower()
    assert "zwaar" not in debuut.lower()


def test_looks_truncated_reason_allows_country_and_duel_endings() -> None:
    assert not looks_truncated_reason(
        "Egypte leunt op Salah als belangrijkste aanvalsbedreiging; "
        "extra aandachtspunt voor Iran."
    )
    assert not looks_truncated_reason(
        "Ghana profiteert van de speelstijl van Panama in dit duel."
    )


def test_humanize_ghana_kudus_counters_not_mane() -> None:
    text = humanize_matchup_shorthand(
        "Ghana Kudus counters.",
        "Ghana",
        team_nl="Kroatië",
        kind="risk",
    )
    assert "Kudus" in text
    assert "Mané" not in text


def test_humanize_bielsa_only_for_uruguay_coach() -> None:
    text = humanize_team_spark(
        "Bielsa Uruguay counters achter backs.",
        "Spanje",
    )
    assert "bondscoach van Spanje" not in text


def test_humanize_mane_counters_and_debut() -> None:
    mane = humanize_matchup_shorthand(
        "Senegal Mane counters.",
        "Senegal",
        team_nl="Frankrijk",
        kind="risk",
    )
    assert "Mané" in mane or "Mane" in mane
    assert "Frankrijk" in mane
    assert mane.count(".") >= 1

    debut = humanize_matchup_shorthand(
        "Uzbekistan debut.",
        "Oezbekistan",
        team_nl="Congo",
        kind="risk",
    )
    assert "eerste WK" in debut.lower() or "zenuw" in debut.lower()


def test_humanize_sweden_isak_matchup_risk_not_profiteert() -> None:
    text = humanize_matchup_shorthand(
        "Zweden Isak/Gyökeres.",
        "Zweden",
        team_nl="Nederland",
        kind="risk",
    )
    assert "profiteert" not in text.lower()
    assert "Zweden" in text
    assert "Nederland" in text


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


def test_haiti_isidor_spark_readable() -> None:
    text = humanize_team_spark(
        "Wilson Isidor (Sunderland) en Bellegarde (Wolves) vormen onverwachte Europese kernspelers.",
        "Haïti",
    )
    assert "Wilson Isidor" in text
    assert "Sunderland" in text
    assert "Bellegarde" in text
    assert "club " not in text.lower()


def test_opponent_zwakker_vs_subject_not_self_weak() -> None:
    text = humanize_factor_reason(
        "Zwakker vs Argentinië balrust en Messi.",
        factor_id="opponent_profile_weak",
        subject_team="Argentinië",
        opponent_team="Oostenrijk",
    )
    assert "Argentinië is kwetsbaar voor Argentinië" not in text
    assert "Oostenrijk" in text
    assert "balrust" in text.lower()


def test_argentina_crowd_vs_not_split_as_matchup() -> None:
    text = humanize_factor_reason(
        "Grote Argentijnse gemeenschap in de VS geeft Argentinië in veel stadions extra steun.",
        factor_id="crowd_bias",
        subject_team="Argentinië",
        opponent_team="Algerije",
    )
    assert "in dit duel speelt mee" not in text.lower()
    assert "in de tegen geeft" not in text.lower()
    assert "in de VS" in text


def test_south_africa_opener_away_at_mexico_not_cohost() -> None:
    text = humanize_factor_reason(
        "Opener op 2240m vs co-host Mexico",
        factor_id="opener_context",
        subject_team="Zuid-Afrika",
        opponent_team="Mexico",
    )
    assert "opent als co-host" not in text.lower()
    assert "tegen co-host Mexico" in text


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


def test_clip_research_excerpt_avoids_mid_word_cut() -> None:
    spark = (
        "Mohamed Ouahbi volgde Walid Regragui op in maart 2026, ongeveer twaalf "
        "weken voor het WK. De staf moet het succesvolle plan uit 2022 (compact spelen, "
        "snelle counters) opnieuw vormgeven met weinig voorbereidingstijd."
    )
    clipped = clip_research_excerpt(spark, max_len=160)
    assert not looks_truncated_reason(clipped)
    assert looks_truncated_reason("snelle cou.")
    assert "WK" in clipped


def test_ouahbi_spark_humanized() -> None:
    text = humanize_research_line(
        "Mohamed Ouahbi volgde Walid Regragui op, snelle cou.",
        team_nl="Marokko",
    )
    assert "counters" in text.lower()
    assert "cou." not in text


def test_away_fixture_humanized() -> None:
    text = humanize_factor_reason(
        "Uit tegen co-host Canada (Toronto Stadium).",
        factor_id="away_fixture",
        subject_team="Bosnië-Herzegovina",
        opponent_team="Canada",
    )
    assert "heeft last van" not in text
    assert "uit tegen co-host canada" in text.lower()
    assert "toronto" in text.lower()
