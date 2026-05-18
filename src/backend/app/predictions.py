from dataclasses import dataclass

from app.teams import display_team_name


PICKS = ("1", "2", "3")

# Nederlandse poule-termen (geen vage "outsider").
TIER_FAVORIET = "Favoriet"
TIER_KANDIDAAT = "Kandidaat"
TIER_STERKE_UNDERDOG = "Sterke underdog"
TIER_VASTE_UNDERDOG = "Vaste underdog"
TIER_UNDERDOG = "Underdog"
TIER_KLEINE_UNDERDOG = "Kleine underdog"


@dataclass(frozen=True)
class TeamProfile:
    rating: int
    tier: str
    style: str
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    niche: tuple[str, ...]


DEFAULT_PROFILE = TeamProfile(
    rating=62,
    tier=TIER_UNDERDOG,
    style="compact spelen, momenten kiezen en leunen op wedstrijdenergie",
    strengths=("organisatie", "fysieke duels", "standaardsituaties"),
    risks=("minder individuele topkwaliteit", "kan moeite hebben als het zelf het spel moet maken"),
    niche=("wedstrijdritme en groepsdynamiek wegen hier zwaar",),
)


TEAM_PROFILES: dict[str, TeamProfile] = {
    "Argentina": TeamProfile(91, "Favoriet", "ervaren, pragmatisch en sterk in beslissende fases", ("wereldklasse in de as", "toernooi-ervaring", "wedstrijdcontrole"), ("leunt soms op kleine marges", "tempo kan zakken tegen energieke tegenstanders"), ("veel spelers kennen elkaars rollen uit meerdere eindtoernooien",)),
    "France": TeamProfile(92, "Favoriet", "explosief, atletisch en diep in elke linie", ("selectiebreedte", "transitiegevaar", "knock-out ervaring"), ("kan soms slordig worden bij veel balbezit", "verwachtingsdruk"), ("veel profielen die een wedstrijd individueel kunnen kantelen",)),
    "Brazil": TeamProfile(90, "Favoriet", "technisch dominant met veel aanvallende variatie", ("creativiteit", "1-tegen-1 kwaliteit", "aanvallende diepte"), ("balans bij counters", "druk rond grote toernooien"), ("kan via individuele acties door gesloten blokken heen breken",)),
    "Spain": TeamProfile(89, "Favoriet", "possession, pressing en controle via middenveld", ("balcontrole", "pressing", "technische zekerheid"), ("kan kwetsbaar zijn als kansen niet snel vallen", "ruimte achter de backs"), ("synergie uit herkenbare Spaanse school en clubconnecties",)),
    "England": TeamProfile(88, "Favoriet", "hoog individueel niveau met veel scorend vermogen", ("aanvalskwaliteit", "squad depth", "standaardsituaties"), ("toernooidruk", "balans tussen voorzichtigheid en initiatief"), ("veel spelers gewend aan hoge intensiteit in de Premier League",)),
    "Portugal": TeamProfile(87, "Kandidaat", "technisch sterk en flexibel tussen controle en counters", ("creatieve middenvelders", "diepte in de selectie", "ervaring"), ("kan afhankelijk worden van momenten", "defensieve restverdediging"), ("mix van jonge energie en ervaren leiderschap",)),
    "Germany": TeamProfile(86, "Kandidaat", "gestructureerd, fysiek en gevaarlijk in momentumfases", ("wedstrijdritme", "druk zetten", "toernooi-DNA"), ("recente wisselvalligheid", "ruimte in omschakeling"), ("Duitse teams kunnen in toernooien vaak boven vorm uitstijgen",)),
    "Netherlands": TeamProfile(85, "Kandidaat", "compact, tactisch en sterk in omschakeling", ("defensieve kwaliteit", "luchtduels", "coachbare structuur"), ("creativiteit tegen lage blokken", "efficiëntie voor goal"), ("veel spelers zijn gewend aan tactisch strakke clubsystemen",)),
    "Belgium": TeamProfile(82, TIER_STERKE_UNDERDOG, "technisch, ervaren en gevaarlijk tussen de linies", ("aanvallende kwaliteit", "ervaring", "passing"), ("generatiewissel", "snelheid achterin"), ("oude automatismen en nieuwe rollen moeten samenvallen",)),
    "Croatia": TeamProfile(82, TIER_STERKE_UNDERDOG, "ervaren, geduldig en extreem comfortabel in spannende wedstrijden", ("middenveldcontrole", "toernooi-rust", "mentale hardheid"), ("leeftijd en intensiteit", "minder pure snelheid"), ("kan wedstrijden lang in leven houden en laat beslissingen laat vallen",)),
    "Uruguay": TeamProfile(82, TIER_STERKE_UNDERDOG, "agressief, direct en competitief", ("fysieke intensiteit", "aanvallende power", "duelkracht"), ("discipline", "ruimte bij hoge druk"), ("Zuid-Amerikaanse wedstrijdhardheid maakt ze lastig in knock-outachtige duels",)),
    "Morocco": TeamProfile(81, TIER_STERKE_UNDERDOG, "compact, volwassen en gevaarlijk vanuit transitie", ("organisatie", "mentale energie", "counters"), ("kan moeite hebben met favorietenrol", "kansenvolume"), ("WK 2022 liet zien dat dit team comfortabel is als underdog",)),
    "Colombia": TeamProfile(80, TIER_STERKE_UNDERDOG, "technisch, fel en aanvallend creatief", ("vormgolven", "creativiteit", "fysieke intensiteit"), ("wedstrijdcontrole", "emotionele momenten"), ("kan vanuit sfeer en momentum snel boven zichzelf uitstijgen",)),
    "Switzerland": TeamProfile(79, TIER_VASTE_UNDERDOG, "gedisciplineerd, volwassen en moeilijk kapot te spelen", ("organisatie", "ervaring", "compactheid"), ("minder explosieve aanval", "moeite met openbreken"), ("vaak sterker dan de namen op papier suggereren",)),
    "USA": TeamProfile(78, TIER_VASTE_UNDERDOG, "atletisch, direct en energiek", ("intensiteit", "thuisregio", "loopvermogen"), ("eindpass", "controle onder druk"), ("WK in eigen regio kan extra energie en ritme geven",)),
    "Mexico": TeamProfile(77, TIER_VASTE_UNDERDOG, "emotioneel geladen, intens en thuisregio-gedreven", ("publieksenergie", "ervaring", "duelkracht"), ("druk op de ploeg", "creativiteit tegen lage blokken"), ("openingswedstrijd en Mexicaanse omstandigheden kunnen veel invloed hebben",)),
    "Japan": TeamProfile(77, TIER_VASTE_UNDERDOG, "snel, technisch en tactisch volwassen", ("pressing", "teamdiscipline", "tempo"), ("fysieke duels", "afmaken van kansen"), ("sterke collectieve automatismen compenseren soms sterverschil",)),
    "Senegal": TeamProfile(77, TIER_VASTE_UNDERDOG, "fysiek sterk en gevaarlijk in omschakeling", ("atletiek", "duelkracht", "directe dreiging"), ("creatieve controle", "consistentie"), ("kan favorieten ongemakkelijk maken met tempo en duels",)),
    "Türkiye": TeamProfile(76, TIER_UNDERDOG, "emotioneel, technisch en grillig", ("creativiteit", "afstandsschoten", "wedstrijdenergie"), ("stabiliteit", "defensieve ruimtes"), ("momentum speelt bij Turkije vaak opvallend zwaar mee",)),
    "Austria": TeamProfile(76, TIER_UNDERDOG, "intens, georganiseerd en pressend", ("collectief drukzetten", "discipline", "fitheid"), ("individuele topkwaliteit", "kansen creëren tegen lage blokken"), ("coachcontinuïteit en systeemvastheid zijn belangrijke pluspunten",)),
    "Sweden": TeamProfile(75, TIER_UNDERDOG, "fysiek, direct en sterk in organisatie", ("luchtduels", "discipline", "standaardsituaties"), ("tempo in balbezit", "creativiteit"), ("kan wedstrijden vertragen en tegenstanders uit ritme halen",)),
    "Norway": TeamProfile(75, TIER_UNDERDOG, "topzwaar met veel dreiging in de voorhoede", ("elite-afwerking", "fysiek voorin", "direct spel"), ("balans in de ploeg", "toernooi-ervaring"), ("als de aanvoer naar de spitsen klopt, stijgt de win-kans snel",)),
    "Ecuador": TeamProfile(74, TIER_UNDERDOG, "fysiek, energiek en lastig in duels", ("intensiteit", "jonge kern", "transities"), ("ervaring in late fases", "controle"), ("hoog tempo en atletiek kunnen technisch sterkere teams verstoren",)),
    "Côte d'Ivoire": TeamProfile(74, TIER_UNDERDOG, "krachtig, direct en gevaarlijk in open wedstrijden", ("fysiek", "aanvallende power", "duels"), ("organisatie", "consistentie"), ("Afrikaanse toernooi-energie en fysieke profielen maken ze gevaarlijk",)),
    "Paraguay": TeamProfile(72, TIER_UNDERDOG, "hard, compact en wedstrijdslim", ("duels", "verdedigende organisatie", "standaardsituaties"), ("aanvallende variatie", "balbezit onder druk"), ("kan favorieten frustreren door tempo en ruimtes klein te maken",)),
    "Canada": TeamProfile(72, TIER_UNDERDOG, "snel, atletisch en direct", ("snelheid", "thuisregio", "omschakeling"), ("ervaring", "defensieve stabiliteit"), ("Noord-Amerikaanse omstandigheden kunnen in hun voordeel werken",)),
    "Australia": TeamProfile(71, TIER_UNDERDOG, "fysiek, compact en mentaal taai", ("discipline", "duelkracht", "teamgeest"), ("creativiteit", "kansenvolume"), ("vaak beter in toernooiwedstrijden dan in losse ratings",)),
    "Scotland": TeamProfile(71, TIER_UNDERDOG, "intens, fysiek en collectief", ("teamspirit", "duels", "standaardsituaties"), ("aanvallende verfijning", "diepte in selectie"), ("kan via chaos en energie wedstrijden openbreken",)),
    "Czechia": TeamProfile(71, TIER_UNDERDOG, "gedisciplineerd, fysiek en direct", ("organisatie", "duels", "standaardsituaties"), ("creativiteit", "tempo achterin"), ("comfortabel in wedstrijden waarin details beslissen",)),
    "Ghana": TeamProfile(70, TIER_UNDERDOG, "fysiek, explosief en onvoorspelbaar", ("atletiek", "transitie", "individuele momenten"), ("controle", "defensieve samenhang"), ("kan via tempo en duelkracht snel momentum pakken",)),
    "Algeria": TeamProfile(70, TIER_UNDERDOG, "technisch en emotioneel geladen", ("creativiteit", "ervaring", "wedstrijdenergie"), ("consistentie", "ruimte achter druk"), ("Noord-Afrikaanse flair maakt ze gevaarlijk in losse wedstrijden",)),
    "Egypt": TeamProfile(70, TIER_UNDERDOG, "ervaren en compact met individuele dreiging", ("ervaring", "discipline", "aanvallende sterkwaliteit"), ("tempo", "diepte in selectie"), ("kan lang in wedstrijden blijven en wachten op één moment",)),
    "Korea Republic": TeamProfile(70, TIER_UNDERDOG, "snel, gedisciplineerd en hard werkend", ("loopvermogen", "organisatie", "transities"), ("fysieke mismatch", "creativiteit centraal"), ("collectieve discipline maakt het verschil tegen gelijkwaardige teams",)),
    "IR Iran": TeamProfile(69, TIER_UNDERDOG, "compact, fysiek en countergericht", ("organisatie", "duels", "directe counters"), ("balbezit", "creativiteit"), ("kan wedstrijden gesloten houden en de underdogrol goed spelen",)),
    "Tunisia": TeamProfile(68, TIER_UNDERDOG, "compact, fel en defensief gedisciplineerd", ("organisatie", "duels", "teamdiscipline"), ("scorend vermogen", "risico nemen"), ("kan favorieten lang frustreren als het eerste doelpunt uitblijft",)),
    "Saudi Arabia": TeamProfile(68, TIER_UNDERDOG, "energiek, technisch en agressief in drukmomenten", ("intensiteit", "brutale momenten", "teamenergie"), ("consistentie", "ruimte achterin"), ("kan in één wedstrijd veel gevaarlijker zijn dan de rating suggereert",)),
    "Qatar": TeamProfile(66, TIER_UNDERDOG, "compact en gewend aan toernooivoetbal in korte periodes", ("organisatie", "ervaring samen", "discipline"), ("tempo", "individuele topkwaliteit"), ("veel spelers hebben vaak in vergelijkbare nationale structuur gespeeld",)),
    "South Africa": TeamProfile(66, TIER_UNDERDOG, "energiek, fysiek en opportunistisch", ("wedstrijdenergie", "duels", "counters"), ("controle", "efficiëntie"), ("kan profiteren als de tegenstander onder openingsdruk staat",)),
    "Uzbekistan": TeamProfile(65, TIER_KLEINE_UNDERDOG, "gestructureerd, hardwerkend en compact", ("discipline", "organisatie", "teamcohesie"), ("ervaring op dit podium", "aanvallende topkwaliteit"), ("eerste WK-context kan extra energie geven, maar ook nervositeit",)),
    "Congo DR": TeamProfile(65, TIER_KLEINE_UNDERDOG, "fysiek sterk en gevaarlijk in losse fases", ("atletiek", "duels", "directheid"), ("organisatie", "balvaste controle"), ("kan met fysieke mismatch wedstrijden kantelen",)),
    "Bosnia and Herzegovina": TeamProfile(65, TIER_KLEINE_UNDERDOG, "technisch in fases en afhankelijk van sleutelspelers", ("ervaring", "passing", "momentenkwaliteit"), ("tempo", "diepte in selectie"), ("als de ervaren kern controle vindt, wordt het een lastige matchup",)),
    "Iraq": TeamProfile(64, TIER_KLEINE_UNDERDOG, "compact, fel en emotioneel sterk", ("teamenergie", "duels", "organisatie"), ("kansen creëren", "ervaring tegen elite"), ("kan vanuit underdogpositie lang overleven in wedstrijden",)),
    "New Zealand": TeamProfile(62, TIER_KLEINE_UNDERDOG, "fysiek, simpel en collectief", ("luchtduels", "discipline", "teamspirit"), ("technische controle", "tempo tegen toplanden"), ("standaardsituaties zijn relatief belangrijk voor hun kans",)),
    "Jordan": TeamProfile(62, TIER_KLEINE_UNDERDOG, "compact, reactief en energiek", ("organisatie", "counters", "teamdiscipline"), ("balbezit onder druk", "selectiediepte"), ("kan verrassen als het lang 0-0 blijft",)),
    "Panama": TeamProfile(61, TIER_KLEINE_UNDERDOG, "fysiek en direct", ("duels", "energie", "standaardsituaties"), ("controle", "creatieve kwaliteit"), ("regionale omstandigheden kunnen helpen tegen niet-Amerikaanse landen",)),
    "Haiti": TeamProfile(60, TIER_KLEINE_UNDERDOG, "direct, atletisch en emotioneel", ("snelheid", "fysiek", "verrassingswaarde"), ("organisatie", "toernooi-ervaring"), ("chaotische wedstrijden vergroten hun upset-kans",)),
    "Cabo Verde": TeamProfile(60, TIER_KLEINE_UNDERDOG, "compact en trots, met focus op omschakeling", ("teamspirit", "organisatie", "transitie"), ("selectiediepte", "ervaring"), ("kleine landen kunnen juist gevaarlijk zijn als niemand ze comfortabel vindt",)),
    "Curaçao": TeamProfile(59, TIER_KLEINE_UNDERDOG, "technisch in momenten en afhankelijk van discipline", ("verrassingswaarde", "individuele momenten", "compactheid"), ("diepte", "ervaring tegen toplanden"), ("Nederlandse voetbalinvloeden kunnen tactisch helpen",)),
}


def is_known_team(team: str) -> bool:
    return team != "To be announced" and not team[:1].isdigit()


def profile_for(team: str) -> TeamProfile:
    return TEAM_PROFILES.get(team, DEFAULT_PROFILE)


def team_insight(team: str) -> dict[str, object] | None:
    if not is_known_team(team):
        return None

    profile = profile_for(team)
    return {
        "team": team,
        "tier": profile.tier,
        "style": profile.style,
        "strengths": list(profile.strengths),
        "risks": list(profile.risks),
        "niche": list(profile.niche),
        "summary": _team_summary(team, profile),
    }


def predict_match(home_team: str, away_team: str, stage: str, round_name: str, group: str | None) -> dict[str, object]:
    if not is_known_team(home_team) or not is_known_team(away_team):
        return {
            "pick": "3",
            "confidence": 0,
            "explanation": "De AI wacht met inhoudelijke voorspelling tot beide landen bekend zijn.",
            "status": "pending",
            "themes": ["Teams nog onbekend"],
            "homeWinProbability": None,
            "drawProbability": None,
            "awayWinProbability": None,
        }

    home = profile_for(home_team)
    away = profile_for(away_team)
    context = _context_bonus(home_team, away_team, stage, round_name, group)
    diff = (home.rating + context["home"]) - (away.rating + context["away"])
    can_draw = stage == "group"

    if can_draw and abs(diff) <= 4:
        pick = "3"
    else:
        pick = "1" if diff >= 0 else "2"

    probabilities = _probabilities(diff, can_draw)
    confidence = _confidence_from_probabilities(pick, probabilities)
    themes = _match_themes(home_team, away_team, home, away, context["themes"], diff, stage)

    return {
        "pick": pick,
        "confidence": confidence,
        "explanation": _match_explanation(home_team, away_team, home, away, pick, themes, stage, round_name),
        "status": "pending",
        "themes": themes[:5],
        "homeWinProbability": probabilities["home"],
        "drawProbability": probabilities["draw"] if can_draw else None,
        "awayWinProbability": probabilities["away"],
    }


def _team_summary(team: str, profile: TeamProfile) -> str:
    name = display_team_name(team)
    return (
        f"{name} wordt gezien als {profile.tier.lower()}: {profile.style}. "
        f"Belangrijk zijn vooral {', '.join(profile.strengths[:2])}. "
        f"Risico: {profile.risks[0]}."
    )


def _context_bonus(home_team: str, away_team: str, stage: str, round_name: str, group: str | None) -> dict[str, object]:
    home_bonus = 0
    away_bonus = 0
    themes: list[str] = []

    host_region = {"Mexico", "USA", "Canada"}
    if home_team in host_region:
        home_bonus += 3
        themes.append("thuisregio en publiek")
    if away_team in host_region:
        away_bonus += 3
        themes.append("thuisregio en publiek")

    if stage == "knockout":
        for team, side in ((home_team, "home"), (away_team, "away")):
            if profile_for(team).tier in {TIER_FAVORIET, TIER_KANDIDAAT, TIER_STERKE_UNDERDOG}:
                if side == "home":
                    home_bonus += 2
                else:
                    away_bonus += 2
        themes.append("knock-out ervaring")
    elif group:
        themes.append(f"groepscontext Poule {group}")

    if round_name == "1":
        themes.append("openingswedstrijd en nervositeit")

    return {"home": home_bonus, "away": away_bonus, "themes": themes}


def _probabilities(diff: int, can_draw: bool) -> dict[str, int]:
    if can_draw:
        draw = max(18, min(31, 28 - abs(diff)))
        home = round((100 - draw) * (0.5 + max(-28, min(28, diff)) / 80))
        home = max(15, min(75, home))
        away = 100 - draw - home
        return {"home": home, "draw": draw, "away": away}

    home = round(50 + max(-35, min(35, diff)) * 1.15)
    home = max(18, min(82, home))
    return {"home": home, "draw": 0, "away": 100 - home}


def _confidence_from_probabilities(pick: str, probabilities: dict[str, int]) -> int:
    if pick == "1":
        return probabilities["home"]
    if pick == "2":
        return probabilities["away"]
    return probabilities["draw"]


def _match_themes(
    home_team: str,
    away_team: str,
    home: TeamProfile,
    away: TeamProfile,
    context_themes: list[str],
    diff: int,
    stage: str,
) -> list[str]:
    themes = list(context_themes)
    stronger = home_team if diff >= 0 else away_team
    stronger_profile = home if diff >= 0 else away
    weaker_profile = away if diff >= 0 else home

    themes.append(f"{display_team_name(stronger)}: {stronger_profile.strengths[0]}")
    if abs(diff) <= 5:
        themes.append("kleine marges en kans op gelijkspel")
    if stronger_profile.rating - weaker_profile.rating >= 10:
        themes.append("duidelijk verschil in selectiebreedte")
    if "standaardsituaties" in (*home.strengths, *away.strengths):
        themes.append("standaardsituaties kunnen zwaar wegen")
    if stage == "group":
        themes.append("puntverlies is minder fataal dan in knock-out")

    return themes


def _match_explanation(
    home_team: str,
    away_team: str,
    home: TeamProfile,
    away: TeamProfile,
    pick: str,
    themes: list[str],
    stage: str,
    round_name: str,
) -> str:
    home_name = display_team_name(home_team)
    away_name = display_team_name(away_team)

    if pick == "1":
        choice = home_name
        profile = home
        opponent = away_name
    elif pick == "2":
        choice = away_name
        profile = away
        opponent = home_name
    else:
        return (
            f"De AI ziet {home_name} tegen {away_name} als een wedstrijd met kleine marges. "
            f"Beide landen hebben genoeg pluspunten om fases te controleren, maar ook duidelijke risico's. "
            f"Daarom wegen vorm, eerste goal, standaardsituaties en groepssituatie hier zwaarder dan pure reputatie."
        )

    phase = "knock-outwedstrijd" if stage == "knockout" else f"groepswedstrijd ronde {round_name}"
    return (
        f"De AI kiest {choice} in deze {phase}. De doorslag zit vooral in {profile.strengths[0]}, "
        f"{profile.strengths[1]} en de matchup tegen {opponent}. Tegelijk blijft dit geen harde odd: "
        f"factoren als {themes[0].lower()}, wedstrijdtempo, eerste goal en bankdiepte kunnen de voorspelling kantelen."
    )
