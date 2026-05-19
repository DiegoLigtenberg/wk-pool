"""Normaliseer research-tekst voor UI: geen em-dash, geen cryptische notities."""

from __future__ import annotations

import re

_DASH_CHARS = ("\u2014", "\u2013", "\u2212")  # em-dash, en-dash, minus sign

_JARGON_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bpossession-model\b", re.I), "balbezitspel"),
    (re.compile(r"\bpossession\b", re.I), "balbezit"),
    (re.compile(r"\bwoestijn-federatie\b", re.I), "klein voetballand"),
    (re.compile(r"\bcompacte bond\b", re.I), "compact team"),
    (re.compile(r"\bin het dossier\b", re.I), "bij dit team"),
    (re.compile(r"\bNY/LA\b"), "New York en Los Angeles"),
    (re.compile(r"\bNY/LA/Miami\b"), "New York, Los Angeles en Miami"),
    (re.compile(r"\btweede thuis\b", re.I), "tweede thuisploeg"),
    (re.compile(r"\b2022-formule\b", re.I), "plan uit 2022"),
    (re.compile(r"\bheruitvind\w*\b", re.I), "opnieuw vormgeven"),
    (re.compile(r"\bdiaspora\b", re.I), "gemeenschap in het buitenland"),
    (re.compile(r"\berfgois\b", re.I), "erfenis van"),
    (re.compile(r"\bpress-resistent\b", re.I), "bestand tegen hoge druk"),
    (re.compile(r"\bplot-twist\b", re.I), "onverwachte wending"),
    (re.compile(r"\bNY/LA/Miami\b"), "New York, Los Angeles en Miami"),
    (re.compile(r"\bt\.o\.v\.\b", re.I), "ten opzichte van"),
    (re.compile(r"\bdefinitief OUT\b", re.I), "definitief uitgeschakeld"),
    (re.compile(r"\bOUT\b"), "uitgeschakeld"),
    (re.compile(r"\barm-fit\b", re.I), "schouderblessure"),
    (re.compile(r"\bminuten/arm-fit\b", re.I), "beperkte speeltijd door blessure"),
    (re.compile(r"\bEU-ster\b", re.I), "speler uit Europese topcompetitie"),
    (re.compile(r"\bPL-anker\b", re.I), "speler uit de Premier League"),
    (re.compile(r"\bPPDA\b"), "pressing-intensiteit (PPDA)"),
    (re.compile(r"\bman-press\b", re.I), "strakke man-dekking"),
    (re.compile(r"\bspit-fitheid\b", re.I), "blessureherstel"),
    (re.compile(r"\bmorpht\b", re.I), "wisselt van systeem"),
    (re.compile(r"\bimpact-sub\b", re.I), "invaller met grote impact"),
    (re.compile(r"\bacclimatisatietijd\b", re.I), "acclimatisatietijd"),
    (re.compile(r"\b2240m\b"), "2240 meter hoogte"),
    (re.compile(r"\b≈2240m\b"), "circa 2240 meter hoogte"),
)

_CLUB_PAREN_RE = re.compile(
    r"\(([A-Z][A-Za-zà-ü\-\.]+(?:\s+[A-Z][A-Za-zà-ü\-\.]+)?)\)"
)

_US_VENUE_CITIES = frozenset(
    {
        "Atlanta",
        "Houston",
        "Dallas",
        "Miami",
        "Seattle",
        "Kansas City",
        "Los Angeles",
        "New York",
        "San Francisco",
        "Philadelphia",
        "Boston",
        "Toronto",
        "Vancouver",
        "Monterrey",
        "Guadalajara",
        "Mexico City",
    }
)


def normalize_display_text(text: str, *, ensure_sentence: bool = True) -> str:
    if not text:
        return text
    for dash in _DASH_CHARS:
        text = text.replace(dash, ", ")
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.{2,}", ".", text)
    if ensure_sentence and text and text[-1] not in ".!?":
        text = f"{text}."
    return text


def humanize_research_line(
    text: str,
    *,
    team_nl: str = "",
    opponent_nl: str = "",
) -> str:
    """Zet research-notities om naar leesbare Nederlandse zinnen voor de UI."""
    raw = text.strip()
    if not raw:
        return ""

    cleaned = raw
    for dash in _DASH_CHARS:
        cleaned = cleaned.replace(dash, ", ")
    cleaned = re.sub(r",\s*,", ",", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    for pattern, replacement in _JARGON_REPLACEMENTS:
        cleaned = pattern.sub(replacement, cleaned)

    cleaned = _expand_parentheses(cleaned)
    cleaned = _ensure_bondscoach_labels(cleaned)
    cleaned = _rewrite_known_spark_patterns(cleaned, team_nl=team_nl, opponent_nl=opponent_nl)
    cleaned = _humanize_short_matchup_counter(cleaned, team_nl=team_nl, opponent_nl=opponent_nl)
    cleaned = _rewrite_short_colon_notes(cleaned, team_nl=team_nl, opponent_nl=opponent_nl)

    return normalize_display_text(cleaned)


def _expand_parentheses(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        if re.fullmatch(r"\d{1,2}", inner):
            return f"({inner} jaar)"
        low = inner.lower()
        if low in {"legend", "legende"}:
            return "(clublegende)"
        if low in {"knie"}:
            return "(knieblessure)"
        if low in {"engelsman", "duitser"}:
            return f"({inner})"
        if re.fullmatch(r"\d{1,2},\s*.+", inner):
            return f"({inner.replace(',', ' jaar,', 1)})"
        if inner in _US_VENUE_CITIES:
            return f"(in {inner})"
        if len(inner.split()) == 1 and inner[0].isupper():
            return f"(club {inner})"
        return f"({inner})"

    return _CLUB_PAREN_RE.sub(repl, text)


def _ensure_bondscoach_labels(text: str) -> str:
    text = re.sub(r"\bnieuwe coach\b", "nieuwe bondscoach", text, flags=re.I)
    text = re.sub(r"\b([A-Z][a-zà-ü\-]+)\s+coach\b", r"bondscoach \1", text)
    text = re.sub(r"\bbondscoach\s+bondscoach\b", "bondscoach", text, flags=re.I)
    return text


def _rewrite_known_spark_patterns(
    text: str, *, team_nl: str, opponent_nl: str
) -> str:
    low = text.lower()

    if "lopetegui" in low and team_nl:
        return (
            f"Bondscoach Julen Lopetegui zet bij {team_nl} in op Spaans balbezitspel "
            f"in een zeer compacte ploeg"
        )
    if "son heung-min" in low and "hong" in low:
        return (
            f"Son Heung-min speelt zijn vierde WK; nieuwe bondscoach is "
            f"Hong Myung-bo (legende van het Koreaanse voetbal)"
        )
    if "messi" in low and "titelverdediger" in low and team_nl:
        return (
            f"Lionel Messi (39 jaar) is waarschijnlijk voor het laatst op een WK bij "
            f"{team_nl} als titelverdediger"
        )
    if "haaland" in low and "eerste keer" in low and team_nl:
        return f"Met Erling Haaland speelt {team_nl} eindelijk weer op een WK (sinds 1998)"
    if "ancelotti" in low and team_nl:
        return (
            f"Carlo Ancelotti is de eerste niet-Braziliaanse bondscoach van {team_nl} sinds 1965"
        )
    if "tuchel" in low and "bondscoach" in low and team_nl:
        return f"Thomas Tuchel is de eerste Duitse bondscoach van {team_nl}"
    if "advocaat" in low and team_nl:
        return f"Dick Advocaat (78 jaar) leidt {team_nl} bij hun eerste WK ooit"
    if "xavi simons" in low and team_nl:
        return (
            f"Xavi Simons is definitief uitgeschakeld (knie); dat laat een gat in de "
            f"creatie van {team_nl}"
        )
    if "2240" in low and "co-host" in low and team_nl:
        if team_nl.lower() == "mexico" or (
            "mexico city" in low and "thuispubliek" in low
        ):
            return (
                f"{team_nl} speelt als co-host thuis in Mexico City (circa 2240 meter); "
                f"massaal publiek en vertrouwde hoogte werken in hun voordeel"
            )
        if "tegen" in low or " vs " in low or "opener op" in low:
            return (
                f"{team_nl} speelt de opener op circa 2240 meter hoogte tegen co-host Mexico; "
                f"een zware fysieke test"
            )
        return (
            f"{team_nl} speelt als co-host thuis op grote hoogte (circa 2240 meter); "
            f"dat versterkt het thuisvoordeel"
        )
    if "modrić" in low or "modric" in low:
        return f"Luka Modrić (40 jaar) is nog steeds geselecteerd; zeldzaam op dit niveau"
    if "cannavaro" in low and team_nl:
        return f"Fabio Cannavaro is bondscoach bij het eerste WK van {team_nl}"
    if "potter" in low and "bondscoach" in low and team_nl:
        return f"Graham Potter is de onverwachte Engelse bondscoach van {team_nl}"
    if "bielsa" in low and team_nl:
        return (
            f"Marcelo Bielsa zet als bondscoach van {team_nl} in op extreem hoge druk en pressing"
        )

    return text


_OPPONENT_PLAYER_NOTE_RE = re.compile(
    r"^(?P<country>[A-Za-zÀ-ÿ\s\-']+)(?::|\s+)(?P<player>[A-Za-zÀ-ÿ\-'.]+)\.?$",
    re.I,
)

# Engelse landnamen in research-bullets → NL teamnaam in UI
_COUNTRY_ALIASES: dict[str, str] = {
    "england": "engeland",
    "germany": "duitsland",
    "united states": "verenigde staten",
    "usa": "verenigde staten",
    "south africa": "zuid-afrika",
    "korea republic": "zuid-korea",
    "czechia": "tsjechië",
    "turkiye": "turkije",
    "netherlands": "nederland",
    "new zealand": "nieuw-zeeland",
    "ivory coast": "ivoorkust",
    "cote d'ivoire": "ivoorkust",
    "bosnia and herzegovina": "bosnië-herzegovina",
    "congo dr": "congo",
    "saudi arabia": "saoedi-arabië",
    "norway": "noorwegen",
    "france": "frankrijk",
    "brazil": "brazilië",
    "scotland": "schotland",
    "haiti": "haïti",
    "mexico": "mexico",
    "qatar": "qatar",
    "senegal": "senegal",
    "iran": "iran",
    "jordan": "jordanië",
    "ecuador": "ecuador",
}


def _refers_to_opponent(country: str, opponent_nl: str) -> bool:
    c = country.strip().lower()
    o = opponent_nl.strip().lower()
    if c == o or c in o or o in c:
        return True
    return _COUNTRY_ALIASES.get(c) == o


def _humanize_simons_note(text: str, *, team_nl: str, opponent_nl: str) -> str:
    """Simons-afwezigheid bij Oranje — geen 'Japan leunt op Simons'."""
    low = text.lower()
    if team_nl == "Nederland":
        return (
            "Nederland speelt deze wedstrijd zonder Xavi Simons (knie); "
            "dat verzwakt de creatie van Oranje."
        )
    if team_nl == "Japan" and ("nederland" in low or "nl " in low or low.startswith("nl ")):
        return (
            "Nederland mist Xavi Simons in de opener; "
            "Japan kan daardoor meer ruimte krijgen in de aanval."
        )
    return (
        "Xavi Simons is niet beschikbaar voor Nederland (knie); "
        "dat verandert de balans in dit duel."
    )


def _humanize_moriyasu_press_note(
    text: str, *, team_nl: str, opponent_nl: str
) -> str | None:
    low = text.lower()
    if "moriyasu" not in low or "press" not in low:
        return None
    japan = opponent_nl if opponent_nl == "Japan" else "Japan"
    if team_nl == "Nederland":
        return (
            f"{japan} zet onder bondscoach Moriyasu hoog druk aan; "
            f"dat maakt de opbouw van Nederland lastig."
        )
    if team_nl == "Japan":
        return (
            "Japan past het pressing-plan van Moriyasu toe; "
            "Nederland moet compact blijven om ruimte te beperken."
        )
    if "oranje" in low or "nederland" in low:
        return (
            "Japan zet onder Moriyasu hoog druk aan tegen het compacte blok van Oranje."
        )
    return f"{japan} zet hoog druk aan onder leiding van Moriyasu."


def _humanize_short_matchup_counter(text: str, *, team_nl: str, opponent_nl: str) -> str:
    """Korte matchup-bullets → volledige zinnen voor de UI."""
    t = text.strip().rstrip(".")
    who = team_nl or "ons"
    low = t.lower()

    moriyasu = _humanize_moriyasu_press_note(
        t, team_nl=team_nl, opponent_nl=opponent_nl
    )
    if moriyasu:
        return moriyasu

    if "simons" in low:
        return _humanize_simons_note(t, team_nl=team_nl, opponent_nl=opponent_nl)

    if any(marker in low for marker in ("zonder", "absent", "out", "→")) and len(t.split()) > 3:
        return text

    if re.fullmatch(r"[A-Za-zÀ-ÿ\s\-']+\s+test", t, re.I) and team_nl:
        country = t.rsplit(maxsplit=1)[0]
        return f"De wedstrijd tegen {country} geldt als zware test voor {who}."

    vs_match = re.match(r"^(.+?)\s+vs\s+(.+)$", t, re.I)
    if vs_match and team_nl:
        left, right = vs_match.group(1).strip(), vs_match.group(2).strip()
        return (
            f"In dit duel speelt mee: {left} tegen {right}; "
            f"dat vraagt extra aandacht van {who}."
        )

    if " vs " in t.lower() and team_nl and len(t) < 80:
        return f"{t}; dat maakt het lastiger voor {who}."

    match = _OPPONENT_PLAYER_NOTE_RE.match(t)
    if not match or len(t) > 60 or len(t.split()) > 4:
        return text

    country = match.group("country").strip()
    player = match.group("player").strip()
    if " " in country.strip():
        return text
    low = player.lower()

    if opponent_nl and not _refers_to_opponent(country, opponent_nl):
        if team_nl:
            return (
                f"{country} brengt met {player} extra dreiging mee; "
                f"lastig voor {who} in dit duel tegen {opponent_nl}."
            )
        return text

    opp = opponent_nl or country
    if low == "caicedo":
        return (
            f"{opp} leunt op Moisés Caicedo op het middenveld (Chelsea); "
            f"lastig duel in het centrum voor {who}"
        )
    if low in {"pressing", "press"} or low.endswith(" press"):
        return f"{opp} zet intens pressing neer; dat verstoort de opbouw van {who}"
    if low in {"nagelsmann", "tuchel", "ancelotti", "scaloni", "bielsa", "lopetegui"}:
        return (
            f"{opp} heeft met coach {player} een duidelijk tactisch plan; "
            f"lastig voor {who} om dat te ontwrichten"
        )
    if low in {"mbappé", "mbappe", "haaland", "vinícius", "vinicius", "messi", "salah"}:
        return (
            f"{opp} leunt op {player} als belangrijkste aanvalsbedreiging; "
            f"extra aandachtspunt voor {who}"
        )
    if team_nl and opponent_nl:
        return (
            f"{opponent_nl} leunt in dit duel op {player}; "
            f"dat vraagt een gericht plan van {who}."
        )
    return text


def _rewrite_short_colon_notes(text: str, *, team_nl: str, opponent_nl: str) -> str:
    """'Tsjechië: Underdog.' → leesbare zin."""
    match = re.fullmatch(r"([A-Za-zÀ-ÿ\s\-]+):\s*([A-Za-zÀ-ÿ\s\-]+)\.?", text.strip())
    if not match or len(text) > 45:
        return text
    subject = match.group(1).strip()
    label = match.group(2).strip()
    label_low = label.lower()
    if label_low in {"underdog", "outsider"}:
        return f"{subject} geldt in dit duel als underdog"
    if opponent_nl and subject.lower() == opponent_nl.lower():
        expanded = _humanize_short_matchup_counter(
            f"{subject} {label}", team_nl=team_nl, opponent_nl=opponent_nl
        )
        if expanded != f"{subject} {label}":
            return expanded
        return f"Tegen {subject}: {label_low}"
    return f"{subject}: {label}"


def humanize_matchup_shorthand(line: str, opponent_nl: str, *, team_nl: str = "") -> str:
    """Zet korte research-bullets om naar leesbare zinnen voor de UI."""
    return humanize_research_line(line, team_nl=team_nl, opponent_nl=opponent_nl)


def humanize_team_spark(notes: str, team_nl: str) -> str:
    """Research-notitie voor teamvisie."""
    return humanize_research_line(notes, team_nl=team_nl)


def is_cryptic_reason(text: str) -> bool:
    clean = text.strip().strip(".")
    return len(clean) < 32 and len(clean.split()) <= 4


_MACHINE_PREFIX_RE = re.compile(
    r"^(tegenstander (kwetsbaar|sterk)|eigen (zwak|sterk)( punt)?|tegenstander)\s*:\s*",
    re.IGNORECASE,
)
_ZWAKWER_RE = re.compile(r"^zwakwer\s+", re.IGNORECASE)


def humanize_factor_reason(
    reason: str,
    *,
    factor_id: str = "",
    subject_team: str = "",
    opponent_team: str = "",
) -> str:
    """Zet factor-redenen uit context_scoring om."""
    text = reason.strip().rstrip(".")
    text = _MACHINE_PREFIX_RE.sub("", text).strip()

    if _ZWAKWER_RE.match(text):
        return normalize_display_text(
            _humanize_zwakwer_line(
                text,
                factor_id=factor_id,
                subject_team=subject_team,
                opponent_team=opponent_team,
            )
        )
    if factor_id == "style_matchup":
        return normalize_display_text(
            _humanize_style_matchup(
                text, subject_team=subject_team, opponent_team=opponent_team
            )
        )

    return humanize_research_line(
        text,
        team_nl=subject_team,
        opponent_nl=opponent_team,
    )


def _humanize_zwakwer_line(
    text: str,
    *,
    factor_id: str,
    subject_team: str,
    opponent_team: str,
) -> str:
    detail = _ZWAKWER_RE.sub("", text).strip()
    low = detail.lower()

    if "giménez" in low or "jiménez" in low:
        center_team = subject_team
        if "mexico" in low and opponent_team:
            center_team = subject_team if "mexico" in subject_team.lower() else opponent_team
        other = opponent_team if center_team == subject_team else subject_team
        if center_team and other:
            return (
                f"In het centrum van {center_team} spelen Giménez en Jiménez: "
                f"{other} haalt daar in dit duel weinig uit"
            )
        return "Het centrale duo Giménez en Jiménez is kwetsbaar, maar de tegenstander profiteert daar weinig van"

    if factor_id == "opponent_profile_weak" and opponent_team:
        return f"{opponent_team} is op dit punt kwetsbaarder dan {subject_team}"
    if factor_id == "tactical_weakness" and subject_team and opponent_team:
        return f"{subject_team} heeft in dit duel moeite met het profiel van {opponent_team}"
    if subject_team:
        return f"{subject_team} is hier zwakker: {detail[0].lower()}{detail[1:]}"
    return f"Zwak punt bij dit team: {detail}"


def _humanize_style_matchup(text: str, *, subject_team: str, opponent_team: str) -> str:
    low = text.lower()
    opp = opponent_team or ""
    if "omschakeling" in low and "compact" in low and opp:
        return f"Snelle omschakeling past bij het lage, compacte blok van {opp}"
    if "compacte counters" in low and opp:
        return f"{opp} kan gevaarlijk omschakelen tegen het aanvalsspel van {subject_team}"
    if "hoge press" in low and opp:
        return f"De hoge druk van {opp} kan de opbouw verstoren"
    if "eigen press" in low and subject_team and opp:
        return (
            f"{subject_team} zet met hoge druk aan; "
            f"{opp} krijgt daardoor weinig rust in de opbouw."
        )
    if "eigen press" in low and opp:
        return f"Hoge druk kan de opbouw van {opp} verstoren"
    return text
