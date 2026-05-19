"""Nederlandse landnamen; FIFA/CSV-identifiers (Engels) blijven interne sleutel."""

from __future__ import annotations

# Canonieke sleutel = naam in fifa-world-cup-2026-UTC.csv / TEAM_PROFILES.
TEAM_NAMES_NL: dict[str, str] = {
    "Algeria": "Algerije",
    "Argentina": "Argentinië",
    "Australia": "Australië",
    "Austria": "Oostenrijk",
    "Belgium": "België",
    "Bosnia and Herzegovina": "Bosnië-Herzegovina",
    "Brazil": "Brazilië",
    "Canada": "Canada",
    "Cabo Verde": "Kaapverdië",
    "Colombia": "Colombia",
    "Congo DR": "Congo",
    "Croatia": "Kroatië",
    "Curaçao": "Curaçao",
    "Czechia": "Tsjechië",
    "Ecuador": "Ecuador",
    "Egypt": "Egypte",
    "England": "Engeland",
    "France": "Frankrijk",
    "Germany": "Duitsland",
    "Ghana": "Ghana",
    "Haiti": "Haïti",
    "IR Iran": "Iran",
    "Iraq": "Irak",
    "Japan": "Japan",
    "Jordan": "Jordanië",
    "Korea Republic": "Zuid-Korea",
    "Mexico": "Mexico",
    "Morocco": "Marokko",
    "Netherlands": "Nederland",
    "New Zealand": "Nieuw-Zeeland",
    "Norway": "Noorwegen",
    "Panama": "Panama",
    "Paraguay": "Paraguay",
    "Portugal": "Portugal",
    "Qatar": "Qatar",
    "Saudi Arabia": "Saoedi-Arabië",
    "Scotland": "Schotland",
    "Senegal": "Senegal",
    "South Africa": "Zuid-Afrika",
    "Spain": "Spanje",
    "Sweden": "Zweden",
    "Switzerland": "Zwitserland",
    "Tunisia": "Tunesië",
    "Türkiye": "Turkije",
    "Uruguay": "Uruguay",
    "USA": "Verenigde Staten",
    "Uzbekistan": "Oezbekistan",
    "Côte d'Ivoire": "Ivoorkust",
}

NL_TO_FIFA: dict[str, str] = {nl: fifa for fifa, nl in TEAM_NAMES_NL.items()}

# Langste FIFA-namen eerst (Bosnia and Herzegovina vóór Bosnia).
_FIFA_NAMES_BY_LENGTH: tuple[str, ...] = tuple(
    sorted(TEAM_NAMES_NL, key=len, reverse=True)
)


def fifa_team_key(team: str) -> str:
    """Engelse CSV-sleutel uit FIFA- of Nederlandse naam."""
    if team in TEAM_NAMES_NL:
        return team
    return NL_TO_FIFA.get(team, team)


def display_team_name(team: str) -> str:
    return TEAM_NAMES_NL.get(fifa_team_key(team), team)


def localize_teams_in_text(text: str) -> str:
    """Vervang bekende FIFA-landnamen in vrije tekst door het Nederlandse equivalent."""
    if not text:
        return text
    out = text
    for fifa_name in _FIFA_NAMES_BY_LENGTH:
        out = out.replace(fifa_name, TEAM_NAMES_NL[fifa_name])
    return out
