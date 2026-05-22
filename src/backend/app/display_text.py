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


def clip_research_excerpt(text: str, max_len: int = 240) -> str:
    """Kort research-fragment af op zin- of woordgrens (niet midden in een woord)."""
    cleaned = text.strip()
    if len(cleaned) <= max_len:
        return cleaned
    chunk = cleaned[:max_len]
    for sep in (". ", "; "):
        pos = chunk.rfind(sep)
        if pos >= int(max_len * 0.55):
            return chunk[: pos + 1].strip()
    if " " in chunk:
        return chunk.rsplit(" ", 1)[0].strip() + "."
    return chunk.strip() + "."


_VALID_SHORT_END_WORDS = frozenset(
    {
        "is",
        "os",
        "us",
        "um",
        "en",
        "er",
        "ar",
        "or",
        "de",
        "te",
        "le",
        "it",
        "at",
        "duel",
        "plan",
        "blok",
        "druk",
        "rust",
        "zone",
        "team",
        "goal",
        "land",
        "steun",
        "vraag",
        "open",
        "gap",
        "zwaar",
        "feest",
        "ooit",
        "haalt",
        "na",
        "host",
        "ploeg",
    }
)

_GENERIC_MATCHUP_EDGE_RE = re.compile(
    r"profiteert van de speelstijl van .+ in dit duel\.?$",
    re.I,
)


def looks_truncated_reason(text: str) -> bool:
    """Heuristiek: YAML/builder heeft waarschijnlijk midden in een zin geknipt."""
    t = text.strip()
    if not t:
        return False
    if re.search(r"\([^)]*$", t) and "=" not in t:
        return True
    if t.endswith(",") or t.endswith(";"):
        return True
    match = re.search(r"\b([A-Za-zÀ-ÿ]{2,5})\.$", t)
    if match:
        word = match.group(1)
        if re.search(rf"[-\u2013]{re.escape(word)}\.$", t, re.I):
            return False
        if word[0].isupper():
            return False
        if word.lower() not in _VALID_SHORT_END_WORDS:
            return True
    return False


def normalize_display_text(text: str, *, ensure_sentence: bool = True) -> str:
    if not text:
        return text
    for dash in _DASH_CHARS:
        text = text.replace(dash, ", ")
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\s+;", ";", text)
    text = re.sub(r"\.{2,}", ".", text)
    if ensure_sentence and text and text[-1] not in ".!?":
        text = f"{text}."
    return text


def humanize_research_line(
    text: str,
    *,
    team_nl: str = "",
    opponent_nl: str = "",
    kind: str = "edge",
) -> str:
    """Zet research-notities om naar leesbare Nederlandse zinnen voor de UI."""
    raw = _strip_research_bullet(text)
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
    cleaned = _humanize_short_matchup_counter(
        cleaned, team_nl=team_nl, opponent_nl=opponent_nl, kind=kind
    )
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
        opp_low = opponent_nl.lower()
        team_low = team_nl.lower()
        # "Qatar onder Lopetegui …" mag niet naar bondscoach van de tegenstander herschrijven.
        if opp_low and opp_low in low and team_low not in low.split("lopetegui", 1)[0]:
            pass
        else:
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
    if "ouahbi" in low and "regragui" in low:
        return (
            "Mohamed Ouahbi volgde Walid Regragui op in maart 2026, ongeveer twaalf weken "
            "voor het WK. De staf moet het succesvolle plan uit 2022 (compact spelen, "
            "snelle counters) opnieuw vormgeven met weinig voorbereidingstijd"
        )
    if "tuchel" in low and "bondscoach" in low and team_nl:
        return f"Thomas Tuchel is de eerste Duitse bondscoach van {team_nl}"
    if "advocaat" in low and team_nl:
        return f"Dick Advocaat (78 jaar) leidt {team_nl} bij hun eerste WK ooit"
    if "isidor" in low and "bellegarde" in low and team_nl:
        return (
            f"{team_nl} leunt op Wilson Isidor (spits bij Sunderland) en "
            f"Jean-Ricner Bellegarde (Wolves) als onverwachte Europese kernspelers."
        )
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
    if "bielsa" in low and team_nl and team_nl.lower() == "uruguay":
        return (
            f"Marcelo Bielsa zet als bondscoach van {team_nl} in op extreem hoge druk en pressing"
        )

    if "we profiteer" in low and team_nl:
        return (
            f"{team_nl} kan profiteren als Qatar compact blijft onder Lopetegui "
            f"en het ritme dicteert."
        )

    if "james rodr" in low and team_nl:
        return (
            "James Rodríguez is blessuregevoelig (schouder) en trainde apart; "
            f"onzeker hoeveel minuten hij voor {team_nl} haalt."
        )

    return text


_OPPONENT_PLAYER_NOTE_RE = re.compile(
    r"^(?P<country>[A-Za-zÀ-ÿ\s\-']+)(?::|\s+)(?P<player>[A-Za-zÀ-ÿ\-'./]+)\.?$",
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
    "türkiye": "turkije",
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
    "croatia": "kroatië",
    "uzbekistan": "oezbekistan",
    "haiti": "haïti",
    "cabo verde": "kaapverdië",
    "cabo": "kaapverdië",
    "mexico": "mexico",
    "qatar": "qatar",
    "senegal": "senegal",
    "iran": "iran",
    "jordan": "jordanië",
    "ecuador": "ecuador",
    "tunisia": "tunesië",
    "belgium": "belgië",
    "egypt": "egypte",
    "iraq": "irak",
    "jordan": "jordanië",
    "norway": "noorwegen",
    "senegal": "senegal",
}


def _refers_to_opponent(country: str, opponent_nl: str) -> bool:
    c = country.strip().lower()
    o = opponent_nl.strip().lower()
    if c == o or c in o or o in c:
        return True
    return _COUNTRY_ALIASES.get(c) == o


def _humanize_simons_note(text: str, *, team_nl: str, opponent_nl: str) -> str:
    """Simons-afwezigheid bij Oranje, geen 'Japan leunt op Simons'."""
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


def _humanize_short_matchup_counter(
    text: str, *, team_nl: str, opponent_nl: str, kind: str = "edge"
) -> str:
    """Korte matchup-bullets → volledige zinnen voor de UI."""
    t = text.strip().rstrip(".")
    who = team_nl or "ons"
    low = t.lower()

    moriyasu = _humanize_moriyasu_press_note(
        t, team_nl=team_nl, opponent_nl=opponent_nl
    )
    if moriyasu:
        return moriyasu

    if "clarke" in low and "compact" in low:
        opp = opponent_nl or "Schotland"
        if team_nl:
            return (
                f"{opp} speelt onder bondscoach Steve Clarke zeer compact; "
                f"daardoor krijgt {team_nl} weinig ruimte om aanvallend te spelen."
            )

    if "simons" in low:
        return _humanize_simons_note(t, team_nl=team_nl, opponent_nl=opponent_nl)

    if any(marker in low for marker in ("zonder", "absent", "out", "→")) and len(t.split()) > 3:
        return text

    if re.fullmatch(r"[A-Za-zÀ-ÿ\s\-']+\s+test", t, re.I) and team_nl:
        country = t.rsplit(maxsplit=1)[0]
        return f"De wedstrijd tegen {country} geldt als zware test voor {who}."

    compact_blok = re.match(r"^(.+?)\s+compact\s+blok\.?$", t, re.I)
    if compact_blok and team_nl and opponent_nl:
        if kind == "edge":
            return (
                f"{opponent_nl} speelt compact; "
                f"{team_nl} kan met geduld en standaards ruimte vinden."
            )
        return (
            f"{opponent_nl} speelt met een compact blok, "
            f"lastig voor {team_nl} om ruimte te vinden."
        )

    vs_match = re.match(r"^(.+?)\s+vs\s+(.+)$", t, re.I)
    if vs_match and team_nl and vs_match.group(1).rstrip().lower().endswith("de"):
        vs_match = None
    if vs_match and team_nl:
        left, right = vs_match.group(1).strip(), vs_match.group(2).strip()
        left_low = left.lower()
        if left_low.startswith(("zwakker", "zwakwer", "sterk", "kwetsbaar")):
            expanded = _humanize_phase_preference_line(
                t,
                factor_id="",
                subject_team=team_nl,
                opponent_team=opponent_nl or right,
            )
            if expanded != t:
                return expanded
        if "compact" in left_low and "blok" in left_low:
            opp = opponent_nl or right
            return f"{team_nl} rekent op een compact blok om {opp} te frustreren in dit duel."
        return (
            f"In dit duel speelt mee: {left} tegen {right}; "
            f"dat vraagt extra aandacht van {who}."
        )

    if "opener" in low and team_nl:
        if "intimiderend" in low and opponent_nl:
            return (
                f"{opponent_nl} is favoriet in de openingswedstrijd; "
                f"dat maakt het mentaal zwaarder voor {team_nl}."
            )
        if "leunt" in low and "opener" in low and team_nl == "Duitsland":
            return (
                "Curaçao speelt zijn WK-debuut in de groepsopener; "
                "Duitsland moet direct tempo en druk neerzetten."
            )

    if " vs " in t.lower() and team_nl and len(t) < 80:
        return f"{t}; dat maakt het lastiger voor {who}."

    if "dekking missen" in low and team_nl:
        return (
            f"{who} kan profiteren als {opponent_nl or 'de tegenstander'} "
            f"dekking mist in de opstelling."
        )
    if "geduld" in low and "/" in t and team_nl:
        parts = re.split(r"\s*/\s*", t)
        return (
            f"{who} verwacht een geduldig duel tegen compacte tegenstanders "
            f"({parts[0].strip()} en {parts[-1].strip()})."
        )
    if "doku" in low and "de bruyne" in low:
        return (
            f"{opponent_nl or 'België'} heeft met Doku en Kevin De Bruyne veel aanvalskracht "
            f"op de flanken; lastig voor {who}."
        )
    if "atletiek" in low and team_nl:
        return (
            f"{opponent_nl or 'Congo'} leunt op fysiek atletische spelers; "
            f"{who} moet het duel lang volhouden."
        )
    if "tier pressing" in low or "haiti-tier" in low:
        return (
            f"{who} krijgt te maken met het hoge pressingspel van "
            f"{opponent_nl or 'Panama en Haïti'}."
        )
    if "rematch" in low and "2022" in low:
        return (
            f"{who} speelt opnieuw tegen een tegenstander uit het WK 2022; "
            f"de halve finale van toen leeft nog na."
        )
    if ("wk-debuut" in low or "wk debuut" in low) and team_nl and opponent_nl:
        return (
            f"{opponent_nl} maakt zijn WK-debuut tegen {team_nl}; "
            f"{team_nl} start als favoriet in de groepsopener."
        )

    match = _OPPONENT_PLAYER_NOTE_RE.match(t)
    if not match or len(t) > 60 or len(t.split()) > 4:
        return text

    country = match.group("country").strip()
    player = match.group("player").strip()
    if country.lower() == "cabo" and player.lower().startswith("verde"):
        country = "Kaapverdië"
        player = player[5:].strip() or player
    if " " in country.strip():
        head, tail = country.rsplit(maxsplit=1)
        if _refers_to_opponent(head, opponent_nl or country):
            country, player = head, f"{tail} {player}".strip()
        else:
            return text
    low = player.lower().rstrip(".")
    full_low = t.lower()

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
    if low in {"compact", "compact blok", "compacte blok"}:
        if kind == "risk":
            return (
                f"{opp} speelt compact; "
                f"lastig voor {who} om ruimte te vinden in dit duel."
            )
        return (
            f"{opp} speelt compact; "
            f"{who} kan met standaards en geduld het blok openbreken."
        )
    if "momentum" in low and "implos" in low:
        if kind == "edge" and team_nl:
            return (
                f"{opp} wisselt grillig van momentum; "
                f"{who} kan op het juiste moment toeslaan."
            )
        return (
            f"{opp} kan onvoorspelbaar wisselen in momentum; "
            f"lastig voor {who} om ritme te houden."
        )
    if "counters" in full_low or low in {"counters", "counter"}:
        if "kudus" in full_low:
            return (
                f"{opp} is gevaarlijk in de omschakeling via Mohammed Kudus; "
                f"extra aandachtspunt voor {who} in de opbouw."
            )
        if "mané" in full_low or "mane" in full_low or country.lower().startswith("senegal"):
            return (
                f"{opp} is gevaarlijk in de omschakeling via Sadio Mané; "
                f"extra aandachtspunt voor {who} in de opbouw."
            )
        return (
            f"{opp} kan gevaarlijk omschakelen; "
            f"{who} moet compact blijven in de opbouw."
        )
    if low in {"debut", "debut-nerves"} or low.startswith("debut"):
        return (
            f"{opp} speelt zijn eerste WK en kan zenuwachtig starten; "
            f"{who} moet direct tempo en structuur neerzetten."
        )
    if "haaland" in full_low and "direct" in full_low:
        return (
            f"{opp} leunt op Erling Haaland als spits met directe diepte; "
            f"lastig voor {who} om ruimte achter de verdediging te houden."
        )
    if "saliba" in full_low and "haaland" in full_low:
        return (
            f"{opponent_nl or 'Frankrijk'} heeft met William Saliba een sterke verdediger "
            f"tegen Erling Haaland; lastig voor {who} om grote kansen te krijgen."
        )
    if player.lower().rstrip(".") == "verde" and opponent_nl:
        return (
            f"{opponent_nl} speelt georganiseerd en compact; "
            f"lastig voor {who} om kansen te creëren."
        )
    if low in {"pressing", "press"} or low.endswith(" press"):
        return f"{opp} zet intens pressing neer; dat verstoort de opbouw van {who}"
    if low in {"nagelsmann", "tuchel", "ancelotti", "scaloni", "lopetegui"}:
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


def _strip_research_bullet(text: str) -> str:
    return re.sub(r"^[-*•]\s+", "", text.strip())


def humanize_matchup_shorthand(
    line: str,
    opponent_nl: str,
    *,
    team_nl: str = "",
    kind: str = "edge",
) -> str:
    """Zet korte research-bullets om naar leesbare zinnen voor de UI.

    kind='edge' → matchup_we_counter (+): voordeel voor team_nl.
    kind='risk' → matchup_counters_us (−): dreiging van opponent_nl voor team_nl.
    """
    line = _strip_research_bullet(line)
    stub = line.strip().rstrip(".")
    words = stub.split()
    if (
        team_nl
        and opponent_nl
        and len(words) == 1
        and len(stub) < 22
        and _refers_to_opponent(stub, opponent_nl)
    ):
        if kind == "edge":
            return humanize_research_line(
                f"{team_nl} heeft tactisch iets meer te bieden dan {opponent_nl} in dit duel.",
                team_nl=team_nl,
                opponent_nl=opponent_nl,
                kind=kind,
            )
        return humanize_research_line(
            f"{opponent_nl} is tactisch lastig voor {team_nl} in dit duel.",
            team_nl=team_nl,
            opponent_nl=opponent_nl,
            kind=kind,
        )
    return humanize_research_line(
        line, team_nl=team_nl, opponent_nl=opponent_nl, kind=kind
    )


def humanize_team_spark(notes: str, team_nl: str) -> str:
    """Research-notitie voor teamvisie."""
    return humanize_research_line(notes, team_nl=team_nl)


def humanize_team_trait_for_insight(tag: str, *, slot: str, team_nl: str) -> str:
    """Korte pool-/YAML-chips (sterktes/risico's) naar leesbare teamvisie-zinnen."""

    raw = tag.strip().rstrip(".")
    if not raw:
        return ""

    low = raw.lower()
    long_form_starts = (
        "kan ",
        "minder ",
        "veel ",
        "als ",
        "vaak ",
        "combinatie ",
        "een ",
        "hun ",
        "dit ",
        "ongeveer ",
    )
    if len(raw) > 48 or any(low.startswith(p) for p in long_form_starts):
        return humanize_research_line(raw, team_nl=team_nl)

    if slot == "strength":
        line = (
            f"Met {raw} maken {team_nl} het tegenstanders lastig — "
            f"daar zoekt dit team vaak zijn beste fases."
        )
    else:
        line = (
            f"Als {raw} niet op niveau is, wordt het snel een lastige middag voor {team_nl} "
            f"(zeker tegen sterkere tegenstanders)."
        )
    return humanize_research_line(line, team_nl=team_nl)


def is_cryptic_reason(text: str) -> bool:
    clean = text.strip().strip(".")
    return len(clean) < 32 and len(clean.split()) <= 4


_MACHINE_PREFIX_RE = re.compile(
    r"^(tegenstander (kwetsbaar|sterk)|eigen (zwak|sterk)( punt)?|tegenstander)\s*:\s*",
    re.IGNORECASE,
)
_ZWAKWER_RE = re.compile(r"^zwakwer\s+", re.IGNORECASE)
_DUEL_MEESPEEL_RE = re.compile(r"^in dit duel speelt mee:\s*", re.IGNORECASE)
_EXTRA_AANDACHT_RE = re.compile(
    r";\s*dat vraagt extra aandacht van [^.]+\.?$",
    re.IGNORECASE,
)


def _strip_baked_duel_phrases(text: str) -> str:
    t = _DUEL_MEESPEEL_RE.sub("", text.strip())
    t = _EXTRA_AANDACHT_RE.sub("", t).strip().rstrip(".")
    return t


def _humanize_phase_preference_line(
    text: str,
    *,
    factor_id: str,
    subject_team: str,
    opponent_team: str,
) -> str:
    """Research-regels uit phase_preferences / opgeslagen context_scoring."""
    t = text.strip().rstrip(".")
    low = t.lower()

    if re.match(r"^brazil group later\.?$", low):
        opp = opponent_team or "Brazilië"
        who = subject_team or "dit team"
        return (
            f"De wedstrijd tegen {opp} komt later in de groep; "
            f"{who} kan zich eerst op de directe tegenstander richten."
        )

    if "courtois" in low and "sanchez" in low and subject_team:
        return (
            "Keepersdilemma Courtois–Sánchez: de bondscoach moet de nummer 1 "
            f"voor het WK nog kiezen, spanning rond {subject_team}."
        )

    if ("st. clair" in low or "st clair" in low) and "crépeau" in low:
        return (
            "Keepersstrijd St. Clair–Crépeau: vlak voor het WK moet Canada "
            "definitief een eerste keeper kiezen."
        )

    if "gemeenschap" in low and any(
        w in low
        for w in ("new york", "los angeles", "diaspora", "ny/la", "in de vs")
    ):
        who = subject_team or "dit team"
        if re.search(r"geeft\s+.+\s+in\s+veel\s+stadions", low):
            return text.strip().rstrip(".") + "."
        adj_match = re.search(
            r"grote\s+([\wà-ÿ\-]+(?:\s+[\wà-ÿ\-]+)?)\s+gemeenschap",
            t,
            re.IGNORECASE,
        )
        adj = adj_match.group(1) if adj_match else ""
        if adj:
            return (
                f"Grote {adj} gemeenschap in de VS geeft {who} "
                f"in veel stadions extra steun."
            )
        return (
            f"Door een grote diaspora in de VS krijgt {who} "
            f"in veel stadions extra steun."
        )

    if "co-host" in low and "thuiswedstrijden" in low and subject_team:
        return (
            f"{subject_team} speelt als co-host meerdere wedstrijden "
            f"in eigen regio met thuispubliek."
        )

    if "james rodriguez" in low or "james rodríguez" in low:
        who = subject_team or "Colombia"
        return (
            "James Rodríguez is blessuregevoelig (schouder) en trainde apart, "
            f"onzeker hoeveel minuten hij voor {who} haalt."
        )

    if "haller" in low and subject_team:
        return (
            "Sébastien Haller is terug na een lang blessuretraject; "
            f"zijn fitheid bepaalt hoe scherp {subject_team} voorin is."
        )

    if "co-host" in low and ("2240" in low or "mexico city" in low or "azteca" in low):
        who = subject_team or "Mexico"
        who_low = who.lower()
        cohost_home = who_low in {"mexico", "verenigde staten", "canada", "united states", "usa"}
        if not cohost_home and opponent_team and opponent_team.lower() in {
            "mexico",
            "verenigde staten",
            "canada",
        }:
            return (
                f"{who} speelt de openingswedstrijd uit tegen co-host {opponent_team} "
                f"op grote hoogte in Mexico City, met massaal thuispubliek voor de thuisploeg."
            )
        return (
            f"{who} opent als co-host op grote hoogte in Mexico City "
            f"met massaal thuispubliek."
        )

    if "co-host" in low and "opener" in low and subject_team and opponent_team:
        return (
            f"{subject_team} opent het WK als co-host tegen {opponent_team}, "
            f"extra druk op het openingsduel."
        )

    if "groep" in low and "opener" in low and subject_team and opponent_team:
        if factor_id == "matchup_edge":
            return (
                f"{opponent_team} wacht het WK-debuut in de groepsopener; "
                f"{subject_team} is favoriet in de openingswedstrijd."
            )
        return (
            f"{subject_team} opent de groep tegen {opponent_team}; "
            f"de eerste wedstrijd telt meteen zwaar."
        )

    if ("sellami" in low or "taamari" in low) and subject_team:
        opp = opponent_team or "de tegenstander"
        return (
            "Jordanië leunt op coach Jamal Sellami en aanvoerder Musa Al-Taamari (Rennes) "
            f"in dit duel tegen {opp}."
        )

    if "2022" in low and "argentin" in low:
        who = subject_team or "Saoedi-Arabië"
        opp = opponent_team or "Argentinië"
        return (
            f"{who} put nog vertrouwen uit de 2-1 zege op {opp} bij het WK 2022 "
            f"richting dit duel."
        )

    zw = re.match(r"^Zwakker (?:tegen|vs)\s+(.+)$", t, re.IGNORECASE)
    if zw and subject_team:
        detail = zw.group(1).strip()
        if (
            factor_id == "opponent_profile_weak"
            and opponent_team
            and detail.lower().startswith(subject_team.lower())
        ):
            rest = detail[len(subject_team) :].strip()
            if rest:
                return (
                    f"{opponent_team} heeft moeite met {subject_team} "
                    f"{rest[0].lower()}{rest[1:]}."
                )
            return f"{opponent_team} heeft moeite met het profiel van {subject_team}."
        if factor_id == "tactical_weakness" and opponent_team:
            if "montella" in detail.lower() or "creatie-gap" in detail.lower():
                return (
                    f"{subject_team} heeft moeite met het hoge tempo en de creatie "
                    f"van {opponent_team} onder Vincenzo Montella."
                )
            return (
                f"{subject_team} heeft moeite met het profiel van {opponent_team}: "
                f"{detail[0].lower()}{detail[1:]}."
            )
        return f"{subject_team} is kwetsbaar voor {detail}."

    sterk = re.match(r"^Sterk\s+(.+?)\s+tegen\s+(.+)$", t, re.IGNORECASE)
    if sterk and subject_team and opponent_team:
        asset = sterk.group(1).strip()
        if factor_id == "opponent_profile_strong":
            return (
                f"{opponent_team} is sterk met {asset}, "
                f"dat maakt het lastig voor {subject_team}."
            )
        if factor_id == "tactical_strength":
            return (
                f"{subject_team} pakt voordeel met {asset} "
                f"in dit duel tegen {opponent_team}."
            )
        return (
            f"{opponent_team} is sterk met {asset}, "
            f"lastig voor {subject_team} in dit duel."
        )

    return text


def _humanize_opponent_profile_weak(
    text: str, *, subject_team: str, opponent_team: str
) -> str | None:
    low = text.strip().lower()
    if low.startswith("zwak tegen") or low.startswith("zwak vs"):
        if "yamal" in low or "bielsa" in low:
            return (
                f"{subject_team} heeft het moeilijk tegen de flanken en hoge druk "
                f"van {opponent_team}."
            )
        return (
            f"{subject_team} is in dit duel kwetsbaarder dan {opponent_team} op papier."
        )
    if not low.startswith("kwetsbaar"):
        return None
    if "ruimte achter" in low and "druk" in low:
        return (
            f"{opponent_team} laat ruimte achter bij hoge druk; "
            f"{subject_team} kan daar tussen de linies profiteren."
        )
    if "messi" in low or "centrum dicht" in low or "geïsoleerd" in low:
        return (
            f"{opponent_team} raakt kwetsbaar als het centrum dicht staat "
            f"en Lionel Messi geïsoleerd wordt; {subject_team} kan daarop inspelen."
        )
    return (
        f"{opponent_team} is op dit punt kwetsbaarder; "
        f"{subject_team} kan dat tactisch benutten."
    )


def humanize_factor_reason(
    reason: str,
    *,
    factor_id: str = "",
    subject_team: str = "",
    opponent_team: str = "",
) -> str:
    """Zet factor-redenen uit context_scoring om."""
    text = _strip_baked_duel_phrases(reason)
    text = _MACHINE_PREFIX_RE.sub("", text).strip().rstrip(".")

    if factor_id == "opponent_profile_weak" and subject_team and opponent_team:
        weak = _humanize_opponent_profile_weak(
            text, subject_team=subject_team, opponent_team=opponent_team
        )
        if weak:
            return normalize_display_text(weak)

    phase = _humanize_phase_preference_line(
        text,
        factor_id=factor_id,
        subject_team=subject_team,
        opponent_team=opponent_team,
    )
    if phase != text:
        return normalize_display_text(phase)

    if _ZWAKWER_RE.match(text):
        return normalize_display_text(
            _humanize_zwakwer_line(
                text,
                factor_id=factor_id,
                subject_team=subject_team,
                opponent_team=opponent_team,
            )
        )
    if factor_id in ("fixture_story", "fixture_narrative", "opener_context"):
        phase = _humanize_phase_preference_line(
            text,
            factor_id=factor_id,
            subject_team=subject_team,
            opponent_team=opponent_team,
        )
        if phase != text:
            return normalize_display_text(phase)

    if factor_id == "matchup_edge" and _GENERIC_MATCHUP_EDGE_RE.search(text):
        if subject_team and opponent_team:
            return normalize_display_text(
                f"{subject_team} heeft tactisch iets meer te bieden dan "
                f"{opponent_team} in dit duel."
            )

    if (
        factor_id == "matchup_edge"
        and opponent_team
        and re.fullmatch(rf"{re.escape(opponent_team)}\.?", text.strip(), flags=re.I)
    ):
        return normalize_display_text(
            f"{subject_team} heeft tactisch iets meer te bieden dan "
            f"{opponent_team} in dit duel."
        )

    if factor_id in ("matchup_edge", "matchup_risk") and "zonder dekking" in text.lower():
        return normalize_display_text(
            f"{subject_team} kan profiteren als de tegenstander hoog drukt zonder dekking achterin"
        )

    if factor_id == "host_region" and subject_team:
        return normalize_display_text(
            f"{subject_team} speelt in eigen regio als co-host met thuispubliek"
        )

    if factor_id == "matchup_edge" and "isidor" in text.lower() and subject_team and opponent_team:
        return normalize_display_text(
            f"{opponent_team} leunt op spits Wilson Isidor (Sunderland); "
            f"{subject_team} moet hem vroeg afdekken."
        )

    if factor_id == "matchup_risk" and "ouahbi" in text.lower() and "hakimi" in text.lower():
        return normalize_display_text(
            "Marokko speelt compact met Hakimi op rechts; nieuwe bondscoach Mohamed "
            "Ouahbi moet het succesvolle WK 2022-plan snel implementeren"
        )

    if factor_id == "home_fixture" and subject_team:
        low = text.lower()
        if low.startswith("thuis in "):
            venue = (
                text[9:]
                .replace("(co-host)", "")
                .replace("(Co-host)", "")
                .strip()
                .rstrip(".")
            )
            return normalize_display_text(
                f"{subject_team} speelt thuis in {venue} als co-host."
            )

    if factor_id == "away_fixture" and subject_team:
        m = re.match(
            r"Uit tegen co-host\s+(.+?)\s*\((.+?)\)\s*\.?$",
            text.strip(),
            re.I,
        )
        if m:
            host_team, venue = m.group(1).strip(), m.group(2).strip()
            return normalize_display_text(
                f"{subject_team} speelt uit tegen co-host {host_team} in {venue}."
            )
        if re.search(r"uit tegen co-host", text, re.I):
            opp = opponent_team or "de tegenstander"
            return normalize_display_text(
                f"{subject_team} speelt uit tegen co-host {opp}, met thuisvoordeel voor de tegenstander."
            )

    if factor_id == "style_matchup":
        return normalize_display_text(
            _humanize_style_matchup(
                text, subject_team=subject_team, opponent_team=opponent_team
            )
        )
    if factor_id == "tactical_strength" and subject_team and opponent_team:
        low = text.lower()
        if "compact" in low and "blok" in low:
            return normalize_display_text(
                f"{subject_team} rekent op een compact blok om {opponent_team} te frustreren."
            )
    if factor_id == "opponent_profile_strong" and subject_team and opponent_team:
        low = text.lower()
        if "compact" in low and (
            "blok" in low
            or "opbouw" in low
            or "moeilijk maken" in low
            or "frustreren" in low
        ):
            return normalize_display_text(
                f"{opponent_team} speelt compact en kan {subject_team} moeilijk maken in de opbouw."
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
        if "yamal" in low or ("bielsa" in low and "press" in low):
            return (
                f"{subject_team} heeft het moeilijk tegen de flanken en hoge druk "
                f"van {opponent_team}."
            )
        return f"{subject_team} heeft in dit duel moeite met het profiel van {opponent_team}"
    if subject_team:
        return f"{subject_team} is hier zwakker: {detail[0].lower()}{detail[1:]}"
    return f"Zwak punt bij dit team: {detail}"


def _humanize_style_matchup(text: str, *, subject_team: str, opponent_team: str) -> str:
    import hashlib

    low = text.lower()
    opp = opponent_team or ""
    sub = subject_team or "dit team"
    if "omschakeling" in low and "compact" in low and opp:
        variants = (
            f"Snelle omschakeling past bij het lage, compacte blok van {opp}.",
            f"{sub} kan met counters het compacte blok van {opp} oprekken.",
            f"{opp} speelt compact; {sub} kan snel omschakelen om ruimte te vinden.",
        )
        idx = int(hashlib.md5(f"{sub}|{opp}".encode()).hexdigest(), 16) % len(variants)
        return variants[idx]
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
    if "t.o.v." in low or "standaardprofiel" in low:
        return (
            f"{subject_team} is sterk op standaards en in de lucht "
            f"tegen {opp}."
        )
    if low.startswith("lucht/") and opp:
        return (
            f"{subject_team} is sterk op standaards en in de lucht "
            f"tegen {opp}."
        )
    return text
